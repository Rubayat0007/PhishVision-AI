"""Tests for the CNN input geometry helpers (torch-free)."""

import pytest

from src.models.geometry import (
    BACKBONE_CHANNELS,
    POOLING_FACTOR,
    flattened_feature_count,
    spatial_size,
)


def test_configured_image_size_matches_expected_geometry():
    assert spatial_size(224) == 28
    assert flattened_feature_count(224) == 128 * 28 * 28


def test_pooling_factor_is_three_two_by_two_stages():
    assert POOLING_FACTOR == 8


def test_default_channel_count():
    assert flattened_feature_count(224) == BACKBONE_CHANNELS * 28 * 28


def test_custom_channels_scale_the_feature_count():
    assert flattened_feature_count(224, channels=64) == 64 * 28 * 28


@pytest.mark.parametrize("size", [1, 100, 225, 230])
def test_sizes_that_do_not_divide_are_rejected(size):
    with pytest.raises(ValueError):
        spatial_size(size)


@pytest.mark.parametrize("size", [0, -8])
def test_non_positive_sizes_are_rejected(size):
    with pytest.raises(ValueError):
        spatial_size(size)


@pytest.mark.parametrize("size", [224.0, "224", None])
def test_non_integer_sizes_are_rejected(size):
    with pytest.raises(TypeError):
        spatial_size(size)


def test_channels_must_be_positive():
    with pytest.raises(ValueError):
        flattened_feature_count(224, channels=0)
