

@workflow.defn
class GenerateHabitImageWorkflow:
    """
    Рабочий процесс для генерации изображения привычки
    """

    @workflow.run
    async def run(
            self,
            habit_id: str,
            user_id: str,
            status: str,
            custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        # Настраиваем политику повторных попыток для активностей
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=2,  # Меньше попыток для генерации изображений
            non_retryable_error_types=["ValueError", "KeyError"]
        )

        # Генерируем изображение
        result = await workflow.execute_activity(
            generate_habit_image,
            retry_policy=retry_policy,
            start_to_close_timeout=timedelta(minutes=5),
            args=[habit_id, user_id, status, custom_prompt]
        )

        return result
