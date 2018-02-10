#from litevideo.input import HDMIIn
from litevideo.output import VideoOut

from gateware import freq_measurement
from gateware import i2c

from targets.utils import csr_map_update, period_ns
from targets.mimasv2.base import BaseSoC as BaseSoC


class VideoSoC(BaseSoC):
    csr_peripherals = (
        "vga_out0",
    )
    csr_map_update(BaseSoC.csr_map, csr_peripherals)

    def __init__(self, platform, *args, **kwargs):
        BaseSoC.__init__(self, platform, *args, **kwargs)

        mode = "rgb"
        if mode == "ycbcr422":
            dw = 16
        elif mode == "rgb":
            dw = 32
        else:
            raise SystemError("Unknown pixel mode.")

        # vga out 0
        vga_out0_pads = platform.request("vga_out", 0)

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

        # self.vga_out0.submodules.i2c = i2c.I2C(vga_out0_pads)

        # all PLL_ADV are used: router needs help...
        # platform.add_platform_command("""INST crg_pll_adv LOC=PLL_ADV_X0Y0;""")
        # FIXME: Fix the HDMI out so this can be removed.
        # platform.add_platform_command(
        #    """PIN "hdmi_out_pix_bufg.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        # platform.add_platform_command(
        #    """PIN "hdmi_out_pix_bufg_1.O" CLOCK_DEDICATED_ROUTE = FALSE;""")
        # We have CDC to go from sys_clk to pixel domain
        #platform.add_platform_command(
#            """
#NET "{pix0_clk}" TNM_NET = "GRPpix0_clk";
#NET "{pix1_clk}" TNM_NET = "GRPpix1_clk";
#""",
#                pix0_clk=self.hdmi_out0.driver.clocking.cd_pix.clk,
#                pix1_clk=self.hdmi_out1.driver.clocking.cd_pix.clk,
#        )
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.vga_out0.driver.clocking.cd_pix.clk)

        for name, value in sorted(self.platform.vga_infos.items()):
            self.add_constant(name, value)


SoC = VideoSoC
