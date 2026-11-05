import argparse

from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator

parser = argparse.ArgumentParser()

parser.add_argument("--issue-width", type=int, default=8)
parser.add_argument("--rob-entries", type=int, default=192)

args = parser.parse_args()

processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    num_cores=1,
    isa=ISA.X86,
)

cpu = processor.get_cores()[0].get_simobject()

cpu.fetchWidth = 8
cpu.decodeWidth = 8
cpu.renameWidth = 8
cpu.dispatchWidth = 8
cpu.issueWidth = args.issue_width
cpu.wbWidth = 8
cpu.commitWidth = 8
cpu.numROBEntries = args.rob_entries

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="32KiB",
    l1i_size="32KiB",
    l2_size="256KiB",
)

memory = SingleChannelDDR4_2400(size="2GiB")

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

binary = BinaryResource(local_path="workloads/matrix_multiply")
board.set_se_binary_workload(binary)

print("\n===== EXPERIMENTAL CONFIGURATION =====")
print("CPU: O3CPU")
print("Issue Width:", args.issue_width)
print("ROB Entries:", args.rob_entries)
print("======================================\n")

simulator = Simulator(board=board)
simulator.run()

print("\nEXPERIMENTAL SIMULATION COMPLETED")
