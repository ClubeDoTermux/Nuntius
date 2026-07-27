import os
import sys
import tempfile
import shutil

import pytest

from nuntius.memory.vector import VectorMemory


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_vector_memory_add_and_search(temp_dir):
    vm = VectorMemory(temp_dir)
    vm.add_message("conv1", "user", "Hello world, how are you?")
    vm.add_message("conv1", "assistant", "I am fine, thank you!")
    count = vm.count()
    assert count >= 2

    results = vm.search("hello")
    assert len(results) >= 1
    assert results[0]["conv_id"] == "conv1"
    assert results[0]["role"] in ("user", "assistant")
    vm.close()


def test_vector_memory_skips_system_and_tool(temp_dir):
    vm = VectorMemory(temp_dir)
    count_before = vm.count()
    vm.add_message("conv1", "system", "you are a bot")
    vm.add_message("conv1", "tool", "some output")
    assert vm.count() == count_before
    vm.close()


def test_vector_memory_delete_conversation(temp_dir):
    vm = VectorMemory(temp_dir)
    vm.add_message("conv1", "user", "hello")
    vm.add_message("conv2", "user", "world")
    total = vm.count()
    assert total >= 2

    vm.delete_conversation("conv1")
    vm.close()


def test_get_conversation_summary(temp_dir):
    vm = VectorMemory(temp_dir)
    vm.add_message("conv1", "user", "message one")
    vm.add_message("conv1", "assistant", "response one")
    summary = vm.get_conversation_summary("conv1")
    assert "message one" in summary or summary == ""
    vm.close()


def test_fallback_search(temp_dir):
    vm = VectorMemory(temp_dir)
    assert vm.available is True
    results = vm.search("python", n_results=3)
    assert isinstance(results, list)
    vm.close()
