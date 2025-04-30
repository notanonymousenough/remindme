import requests
import json
import os  # для чтения API-ключа из переменной окружения (рекомендуется)

def yandex_gpt_request(prompt, api_key, folder_id, model_uri="gpt://b1g3ga6to8fg8a4a9a04/yandexgpt-lite"):
    """
    Отправляет запрос к YandexGPT API и возвращает ответ.

    Args:
        prompt (str): Текст запроса к YandexGPT.
        api_key (str): API-ключ сервисного аккаунта Yandex Cloud.
        folder_id (str): ID вашего каталога в Yandex Cloud.
        model_uri (str, optional): URI модели YandexGPT. Defaults to "gpt://b1g3ga6to8fg8a4a9a04/yandexgpt-lite".

    Returns:
        str: Текст ответа от YandexGPT или сообщение об ошибке.
    """
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "modelUri": model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": 0.6, # Настраивайте температуру по желанию (0.0 - 1.0, ближе к 0 - более детерминированный ответ)
            "maxTokens": 2000  # Максимальное количество токенов в ответе
        },
        "messages": [
            {
                "role": "user",
                "text": prompt
            }
        ],
        "folderId": folder_id  # Обязательно укажите folderId
    })

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Проверка на HTTP ошибки

        data = response.json()
        if 'result' in data and 'message' in data['result']:
            return data['result']['message']['text']
        else:
            return f"Ошибка: Неожиданный формат ответа от API: {data}"

    except requests.exceptions.RequestException as e:
        return f"Ошибка запроса к API: {e}"
    except json.JSONDecodeError as e:
        return f"Ошибка декодирования JSON ответа: {e}. Ответ сервера: {response.text}"
    except Exception as e:
        return f"Произошла общая ошибка: {e}"


if __name__ == "__main__":
    api_key = os.environ.get("YANDEX_API_KEY")  # Чтение API-ключа из переменной окружения
    folder_id = os.environ.get("YANDEX_FOLDER_ID") # Чтение ID каталога из переменной окружения

    if not api_key:
        print("Ошибка: Переменная окружения YANDEX_API_KEY не установлена. Пожалуйста, установите ваш API-ключ.")
        exit(1)
    if not folder_id:
        print("Ошибка: Переменная окружения YANDEX_FOLDER_ID не установлена. Пожалуйста, установите ID вашего каталога Yandex Cloud.")
        exit(1)


    while True:
        user_prompt = input("Введите ваш запрос YandexGPT (или 'выход' для завершения): ")
        if user_prompt.lower() == 'выход':
            break

        response_text = yandex_gpt_request(user_prompt, api_key, folder_id)
        print("\nОтвет YandexGPT:")
        print(response_text)
        print("\n" + "-" * 30 + "\n")
