from app.integrations.checksum import calculate_payload_checksum


def test_payload_checksum_is_independent_of_mapping_order() -> None:
    left = {"name": "Жетыбай", "region": "Маңғыстау", "value": 42}
    right = {"value": 42, "region": "Маңғыстау", "name": "Жетыбай"}

    assert calculate_payload_checksum(left) == calculate_payload_checksum(right)


def test_payload_checksum_changes_when_payload_changes() -> None:
    original = {"name": "Жетыбай", "status": "active"}
    changed = {"name": "Жетыбай", "status": "inactive"}

    assert calculate_payload_checksum(original) != calculate_payload_checksum(changed)
