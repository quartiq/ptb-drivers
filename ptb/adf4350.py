from math import ceil
from fractions import Fraction
import logging


logger = logging.getLogger(__name__)


class ADF4350:
    """From the dtasheet with analogies of naming from
    https://github.com/analogdevicesinc/no-OS/blob/master/drivers/adf4350/adf4350.h
    """

    @staticmethod
    def reg0_fract(x):
        return (x & 0xFFF) << 3

    @staticmethod
    def reg0_int(x):
        return (x & 0xFFFF) << 15

    @staticmethod
    def reg1_mod(x):
        return (x & 0xFFF) << 3

    @staticmethod
    def reg1_phase(x):
        return (x & 0xFFF) << 15

    reg1_prescaler = 1 << 27

    reg2_counter_reset_en = 1 << 3
    reg2_cp_threestate_en = 1 << 4
    reg2_power_down_en = 1 << 5
    reg2_pd_polarity_pos = 1 << 6
    reg2_ldp_6ns = 1 << 7
    reg2_ldp_10ns = 0 << 7
    reg2_ldf_fract_n = 0 << 8
    reg2_ldf_int_n = 1 << 8

    @staticmethod
    def reg2_charge_pump_curr_ua(x):
        return (((x - 312) // 312) & 0xF) << 9

    reg2_double_buff_en = 1 << 13

    @staticmethod
    def reg2_10bit_r_cnt(x):
        return x << 14

    reg2_rdiv2_en = 1 << 24
    reg2_rmult2_en = 1 << 25

    @staticmethod
    def reg2_muxout(x):
        return x << 26

    @staticmethod
    def reg2_noise_mode(x):
        return x << 29

    @staticmethod
    def reg3_12bit_clkdiv(x):
        return x << 3

    @staticmethod
    def reg3_12bit_clkdiv_mode(x):
        return x << 16

    reg3_12bit_csr_en = 1 << 18
    reg3_charge_cancellation_en = 1 << 21
    reg3_anti_backlash_3ns_en = 1 << 22
    reg3_band_sel_clock_mode_high = 1 << 23

    @staticmethod
    def reg4_output_pwr(x):
        return x << 3

    reg4_rf_out_en = 1 << 5

    @staticmethod
    def reg4_aux_output_pwr(x):
        return x << 6

    reg4_aux_output_en = 1 << 8
    reg4_aux_output_fund = 1 << 9
    reg4_aux_output_div = 0 << 9
    reg4_mute_till_lock_en = 1 << 10
    reg4_vco_pwrdown_en = 1 << 11

    @staticmethod
    def reg4_8bit_band_sel_clkdiv(x):
        return x << 12

    @staticmethod
    def reg4_rf_div_sel(x):
        return x << 20

    reg4_feedback_divided = 0 << 23
    reg4_feedback_fund = 1 << 23

    reg5_ld_pin_mode_low = 0 << 22
    reg5_ld_pin_mode_digital = 1 << 22
    reg5_ld_pin_mode_high = 3 << 22

    max_out_freq = 4.4e9  # Hz
    min_out_freq = 34.375e6  # Hz
    min_vco_freq = 2.2e9  # Hz
    max_freq_45_presc = 3e9  # Hz
    max_freq_pfd = 32e6  # Hz
    max_bandsel_clk = 125e3  # Hz
    max_freq_refin = 250e6  # Hz
    max_modulus = 4095
    max_r_cnt = 1023

    ref_frequency = None
    ref_div_factor = None
    ref_doubler_en = False
    ref_div2_en = False

    channel_spacing = 0.
    phase_detector_polarity_positive_en = True
    lock_detect_precision_6ns_en = False
    lock_detect_function_integer_n_en = False
    charge_pump_curr = 2500  # uA
    muxout_select = 0
    low_spur_mode_en = False
    powerdown_en = None

    cycle_slip_reduction_en = True
    charge_cancellation_en = False  # ADF4351
    anti_backlash_3ns_en = False  # ADF4351
    band_select_clock_mode_high_en = False  # ADF4351
    clk_divider_12bit = 150
    clk_divider_mode = 0

    aux_output_en = False
    aux_output_fundamental_en = False
    mute_till_lock_en = False
    output_power = 3
    aux_output_power = 0

    def _f_pfd(self, r_cnt):
        return self.ref_frequency * (1 + self.ref_doubler_en) / (
                r_cnt * (1 + self.ref_div2_en))

    def set_frequency(self, f_out):
        """Set output frequency.

        Args:
            f_out (float): Desired frequency
        Returns:
            Actual output frequency set
        """

        if not (self.min_out_freq <= f_out <= self.max_out_freq):
            raise ValueError("invalid frequency")

        # determine output divider and VCO frequency
        rf_div_sel = 0
        f_vco = f_out
        while f_vco < self.min_vco_freq:
            rf_div_sel += 1
            f_vco *= 2
        assert 0 <= rf_div_sel <= 6
        logger.info("VCO frequency %g GHz", f_vco/1e9)
        logger.info("output divider %i", 1 << rf_div_sel)

        # select prescaler
        prescaler_en = f_vco > self.max_freq_45_presc
        logger.info("prescaler_en %i", prescaler_en)

        # select reference divider and PFD frequency
        r_cnt = self.ref_div_factor
        if not r_cnt:
            r_cnt = ceil(self._f_pfd(1)/self.max_freq_pfd)
        assert 1 <= r_cnt <= self.max_r_cnt
        logger.info("R counter value %i", r_cnt)
        f_pfd = self._f_pfd(r_cnt)
        assert f_pfd <= self.max_freq_pfd
        logger.info("PFD frequency %g MHz", f_pfd/1e6)

        n_int, df = divmod(f_vco, f_pfd)
        n_int = int(n_int)
        n_int_min = 75 if prescaler_en else 23
        assert n_int_min <= n_int <= 1 << 16
        logger.info("N divider integral part %i", n_int)
        logger.info("N divider fractional part %g MHz", df/1e6)
        if df:
            if self.channel_spacing:
                n_mod = int(round(f_pfd/self.channel_spacing))
                while n_mod > self.max_modulus:
                    n_mod //= 2
                n_fract = int(round(df/f_pfd*n_mod))
            else:
                n_rat = Fraction(df/f_pfd)
                logger.info("N divider fraction %s", n_rat)
                n_rat = n_rat.limit_denominator(self.max_modulus)
                n_fract, n_mod = n_rat.numerator, n_rat.denominator
            logger.info("N divider fract/mod %i/%i", n_fract, n_mod)
            logger.info("channel spacing %g kHz", f_pfd/n_mod/1e3)
            logger.info("frequency error %g Hz", f_pfd*n_fract/n_mod - df)
        else:
            n_fract = 0
            n_mod = 1
        assert 1 <= n_mod <= self.max_modulus
        assert 0 <= n_fract < n_mod
        if n_mod > 1:
            assert not self.lock_detect_function_integer_n_en

        # determine clock divider for band selection logic
        band_sel_div = int(f_pfd / self.max_bandsel_clk)
        assert 1 <= band_sel_div <= 255
        logger.info("VCO band selection logic clock divider %i", band_sel_div)

        self._regs = list(range(6))  # control bits

        self._regs[0] |= self.reg0_int(n_int) | self.reg0_fract(n_fract)

        self._regs[1] |= (self.reg1_phase(1) | self.reg1_mod(n_mod) |
                (prescaler_en * self.reg1_prescaler))

        self._regs[2] |= (
                self.reg2_10bit_r_cnt(r_cnt) |
                (0 * self.reg2_double_buff_en) |
                (self.ref_doubler_en * self.reg2_rmult2_en) |
                (self.ref_div2_en * self.reg2_rdiv2_en) |
                (self.phase_detector_polarity_positive_en *
                    self.reg2_pd_polarity_pos) |
                (self.lock_detect_precision_6ns_en * self.reg2_ldp_6ns) |
                (self.lock_detect_function_integer_n_en *
                    self.reg2_ldf_int_n) |
                self.reg2_charge_pump_curr_ua(self.charge_pump_curr) |
                self.reg2_muxout(self.muxout_select) |
                self.reg2_noise_mode(self.low_spur_mode_en*0x3))

        self._regs[3] |= (
                (self.cycle_slip_reduction_en * self.reg3_12bit_csr_en) |
                (self.charge_cancellation_en *
                    self.reg3_charge_cancellation_en) |
                (self.anti_backlash_3ns_en * self.reg3_anti_backlash_3ns_en) |
                (self.band_select_clock_mode_high_en *
                    self.reg3_band_sel_clock_mode_high) |
                self.reg3_12bit_clkdiv(self.clk_divider_12bit) |
                self.reg3_12bit_clkdiv_mode(self.clk_divider_mode))

        self._regs[4] |= (self.reg4_feedback_fund |
                self.reg4_rf_div_sel(rf_div_sel) |
                self.reg4_8bit_band_sel_clkdiv(band_sel_div) |
                self.reg4_rf_out_en |
                self.reg4_output_pwr(self.output_power) |
                self.reg4_aux_output_pwr(self.aux_output_power) |
                (self.aux_output_en * self.reg4_aux_output_en) |
                (self.aux_output_fundamental_en * self.reg4_aux_output_fund) |
                (self.mute_till_lock_en * self.reg4_mute_till_lock_en))

        self._regs[5] |= self.reg5_ld_pin_mode_digital | 0x00180000

        return f_pfd*(n_int + n_fract/n_mod)/(1 << rf_div_sel)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    a = ADF4350()
    a.ref_frequency = 10e6
    a.ref_div_factor = 1
    a.ref_div2_en = False
    a.ref_doubler_en = True

    f = 2e9
    f += 432.1234567e3
    print(a.set_frequency(f))

    print(["{:#010x}".format(r) for r in reversed(a._regs)])
    print(["{:#010x}".format(r) for r in reversed([
            0x00640000,
            0x08008009,
            0x02004E42,
            0x000404B3,
            0x009C803C,
            0x00580005])])
