
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


# =====================================================
# PROJECT 4 - BASELINE X86 O3CPU CONFIGURATION
# =====================================================

# Processor configuration

processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    num_cores=1,
    isa=ISA.X86,
)


# =====================================================
# CACHE CONFIGURATION
# =====================================================

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="32KiB",
    l1i_size="32KiB",
    l2_size="256KiB",
)


# =====================================================
# MAIN MEMORY CONFIGURATION
# =====================================================

memory = SingleChannelDDR4_2400(
    size="2GiB"
)


# =====================================================
# X86 SYSTEM BOARD
# =====================================================

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)


# =====================================================
# WORKLOAD CONFIGURATION
# =====================================================

binary = BinaryResource(
    local_path="workloads/matrix_multiply"
)

board.set_se_binary_workload(binary)


# =====================================================
# SIMULATION
# =====================================================

simulator = Simulator(
    board=board
)


print("\n==============================================")
print("PROJECT 4 - BASELINE X86 O3CPU")
print("==============================================")

print("Architecture : X86")
print("Processor    : O3CPU")
print("Cores        : 1")
print("Clock        : 3 GHz")

print("L1 I-Cache   : 32 KB")
print("L1 D-Cache   : 32 KB")
print("L2 Cache     : 256 KB")

print("Memory       : DDR4-2400")
print("Memory Size  : 2 GiB")

print("Workload     : 128 x 128 Matrix Multiplication")

print("==============================================\n")


simulator.run()


print("\n==============================================")
print("BASELINE SIMULATION COMPLETED")
print("==============================================")

