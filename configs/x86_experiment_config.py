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

# Parse experiment parameters
parser = argparse.ArgumentParser()

parser.add_argument("--issue-width", type=int, default=8)
parser.add_argument("--rob-entries", type=int, default=192)
parser.add_argument("--l2-kb", type=int, default=256)

args = parser.parse_args()

# Processor
processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    num_cores=1,
    isa=ISA.X86,
)

# Access O3 CPU SimObject
cpu = processor.get_cores()[0].get_simobject()

# CPU parameters
cpu.fetchWidth = 8
cpu.decodeWidth = 8
cpu.renameWidth = 8
cpu.dispatchWidth = 8
cpu.issueWidth = args.issue_width
cpu.wbWidth = 8
cpu.commitWidth = 8
cpu.numROBEntries = args.rob_entries

# Cache hierarchy
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="32KiB",
    l1i_size="32KiB",
    l2_size=f"{args.l2_kb}KiB",
)

# Memory
memory = SingleChannelDDR4_2400(size="2GiB")

# Board
board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Workload
binary = BinaryResource(
    local_path="workloads/matrix_multiply"
)

board.set_se_binary_workload(binary)

# Display configuration
print("\n===== EXPERIMENTAL CONFIGURATION =====")
print("CPU: O3CPU")
print("Issue Width:", args.issue_width)
print("ROB Entries:", args.rob_entries)
print("L1 I-Cache: 32KiB")
print("L1 D-Cache: 32KiB")
print("L2 Cache:", f"{args.l2_kb}KiB")
print("======================================\n")

# Run simulation
simulator = Simulator(board=board)
simulator.run()

print("\nEXPERIMENTAL SIMULATION COMPLETED")
