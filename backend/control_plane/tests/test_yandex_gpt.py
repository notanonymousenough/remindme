import pytest
import datetime
from unittest.mock import patch, AsyncMock
import asyncio
import os

from backend.control_plane.utils.clients import yandex_gpt_client, YandexGptAPI
from backend.control_plane.utils import timeutils


@pytest.fixture
def use_real_api():
    """
    Determine whether to use the real API or mocks.
    Set USE_REAL_API=1 environment variable to use real API.
    """
    return os.environ.get("USE_REAL_API", "0") == "1"


@pytest.mark.asyncio
async def test_predict_reminder_time(use_real_api):
    """
    Test reminder prediction with either mocked or real API responses
    """
    user_timezone_offset = 180
    fixed_now = datetime.datetime(2025, 4, 19, 12, 0, tzinfo=datetime.timezone.utc)

    # Test cases with expected inputs
    test_cases = [
        {
            'prompt': 'через час вынести мусор',
            'mocked_response': '{"datetime": "2025-04-19T16:00"}',
        },
        {
            'prompt': 'в среду в 14 написать курсач на тему асинхронных процессов',
            'mocked_response': '{"datetime": "2025-04-23T14:00"}',
        },
    ]

    with patch('backend.control_plane.utils.timeutils.get_utc_now', return_value=fixed_now):
        for case in test_cases:
            if not use_real_api:
                # Mock the private __query method
                method_to_patch = f"_{YandexGptAPI.__name__}__query"
                with patch.object(YandexGptAPI, method_to_patch, AsyncMock(return_value=case['mocked_response'])):
                    # Call the function with mocked API
                    predicted = await yandex_gpt_client.predict_reminder_time(180, case['prompt'])

                    # Calculate expected datetime from the mocked response
                    expected_dt_str = case['mocked_response'].split('"datetime": "')[1].split('"')[0]
                    expected_dt = timeutils.parse_string_in_user_timezone(expected_dt_str, 180, "%Y-%m-%dT%H:%M")

                    # Verify the result
                    assert predicted == expected_dt, f"For prompt '{case['prompt']}'"
                    print(
                        f"Mock test passed for '{case['prompt']}': {timeutils.format_datetime_for_user(predicted, 180)}")
            else:
                # Call the actual API
                predicted = await yandex_gpt_client.predict_reminder_time(user_timezone_offset, case['prompt'])

                # Validate the result is reasonable
                assert isinstance(predicted, datetime.datetime), "Result should be a datetime object"
                assert predicted > fixed_now, "Predicted time should be in the future"

                # Calculate expected user datetime like the mocked response
                expected_dt_str = timeutils.format_datetime_for_user(predicted, user_timezone_offset, "%Y-%m-%dT%H:%M")

                # Validate the result
                assert '{"datetime": "%s"}' % expected_dt_str == case['mocked_response']
                print(
                    f"Real API test passed for '{case['prompt']}': {timeutils.format_datetime_for_user(predicted, user_timezone_offset)}")

