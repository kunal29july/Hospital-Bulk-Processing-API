import pytest
from fastapi import UploadFile, HTTPException
from io import BytesIO
from app.services.csv_processor import CSVProcessor


@pytest.mark.asyncio
async def test_valid_csv():
    """Test parsing a valid CSV file"""
    csv_content = b"name,address,phone\nCity Hospital,123 Main St,555-1234\nGeneral Hospital,456 Oak Ave,555-5678"
    file = UploadFile(filename="test.csv", file=BytesIO(csv_content))
    
    rows, filename = await CSVProcessor.validate_and_parse_csv(file)
    
    assert len(rows) == 2
    assert rows[0]['name'] == "City Hospital"
    assert rows[0]['address'] == "123 Main St"
    assert rows[0]['phone'] == "555-1234"
    assert filename == "test.csv"


@pytest.mark.asyncio
async def test_csv_without_phone():
    """Test parsing CSV without optional phone field"""
    csv_content = b"name,address\nCity Hospital,123 Main St\nGeneral Hospital,456 Oak Ave"
    file = UploadFile(filename="test.csv", file=BytesIO(csv_content))
    
    rows, filename = await CSVProcessor.validate_and_parse_csv(file)
    
    assert len(rows) == 2
    assert rows[0]['phone'] is None


@pytest.mark.asyncio
async def test_csv_missing_required_header():
    """Test CSV with missing required header"""
    csv_content = b"name,phone\nCity Hospital,555-1234"
    file = UploadFile(filename="test.csv", file=BytesIO(csv_content))
    
    with pytest.raises(HTTPException) as exc_info:
        await CSVProcessor.validate_and_parse_csv(file)
    
    assert exc_info.value.status_code == 400
    assert "Missing required header: address" in exc_info.value.detail


@pytest.mark.asyncio
async def test_csv_too_many_rows():
    """Test CSV exceeding max rows limit"""
    # Create CSV with 21 rows (exceeds limit of 20)
    rows = ["name,address,phone"]
    for i in range(21):
        rows.append(f"Hospital {i},Address {i},555-{i:04d}")
    csv_content = "\n".join(rows).encode()
    
    file = UploadFile(filename="test.csv", file=BytesIO(csv_content))
    
    with pytest.raises(HTTPException) as exc_info:
        await CSVProcessor.validate_and_parse_csv(file)
    
    assert exc_info.value.status_code == 400
    assert "maximum allowed is 20" in exc_info.value.detail


@pytest.mark.asyncio
async def test_csv_empty_required_field():
    """Test CSV with empty required field"""
    csv_content = b"name,address,phone\n,123 Main St,555-1234"
    file = UploadFile(filename="test.csv", file=BytesIO(csv_content))
    
    with pytest.raises(HTTPException) as exc_info:
        await CSVProcessor.validate_and_parse_csv(file)
    
    assert exc_info.value.status_code == 400
    assert "'name' is required" in exc_info.value.detail


def test_validate_hospital_data():
    """Test hospital data validation"""
    # Valid data
    valid_row = {"name": "City Hospital", "address": "123 Main St", "phone": "555-1234"}
    is_valid, error = CSVProcessor.validate_hospital_data(valid_row)
    assert is_valid is True
    assert error == ""
    
    # Name too long
    invalid_row = {"name": "A" * 201, "address": "123 Main St", "phone": "555-1234"}
    is_valid, error = CSVProcessor.validate_hospital_data(invalid_row)
    assert is_valid is False
    assert "name too long" in error
