from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from gateware import freq_measurement

from litex.soc.cores.frequency_meter import FrequencyMeter

from litescope import LiteScopeAnalyzer

from targets.utils import csr_map_update, period_ns
from targets.arty.net import NetSoC as BaseSoC


class VideoSoC(BaseSoC):
    csr_peripherals = (
        "vga_out0",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        mode = "ycbcr422"
        if mode == "ycbcr422":
            dw = 16
        elif mode == "rgb":
            dw = 32
        else:
            raise SystemError("Unknown pixel mode.")

        pix_freq = 148.50e6

        # vga out 0
        vga_out0_pads = platform.request("vga_out")

        vga_out0_dram_port = self.sdram.crossbar.get_port(
            mode="read",
            dw=dw,
            cd="pix",
            reverse=True)

        self.submodules.vga_out0 = VideoOut(
            platform.device,
            vga_out0_pads,
            vga_out0_dram_port,
            mode=mode,
            fifo_depth=4096)

        # We have CDC to go from sys_clk to pixel domain
        platform.add_platform_command(
                """
                NET "{pix0_clk}" TNM_NET = "GRPpix0_clk";
                """,
                pix0_clk=self.vga_out0.driver.clocking.cd_pix.clk,
        )

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.vga_out0.driver.clocking.cd_pix.clk)

        self.platform.add_period_constraint(self.vga_out0.driver.clocking.cd_pix.clk, period_ns(1*pix_freq))
        self.platform.add_period_constraint(self.vga_out0.driver.clocking.cd_pix5x.clk, period_ns(5*pix_freq))

        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.vga_out0.driver.clocking.cd_pix.clk,
            self.vga_out0.driver.clocking.cd_pix5x.clk)

        
class VideoSoCDebug(VideoSoC):
    csr_peripherals = (
        "analyzer",
    )
    csr_map_update(VideoSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        VideoSoC.__init__(self, platform, *args, **kwargs)

        # # #

        # leds
        #pix_counter = Signal(32)
        #self.sync.hdmi_in0_pix += pix_counter.eq(pix_counter + 1)
        #self.comb += platform.request("user_led", 0).eq(pix_counter[26])

        #pix1p25x_counter = Signal(32)
        #self.sync.pix1p25x += pix1p25x_counter.eq(pix1p25x_counter + 1)
        #self.comb += platform.request("user_led", 1).eq(pix1p25x_counter[26])

        #pix5x_counter = Signal(32)
        #self.sync.hdmi_in0_pix5x += pix5x_counter.eq(pix5x_counter + 1)
        #self.comb += platform.request("user_led", 2).eq(pix5x_counter[26])


    def do_exit(self, vns):
        self.analyzer.export_csv(vns, "test/analyzer.csv")


SoC = VideoSoC
