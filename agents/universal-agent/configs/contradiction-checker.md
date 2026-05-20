# Role
Проверщик противоречий

## Agent Type
contradiction-checker

## Input Topic
legal.answer.raw

## Output Topic
legal.answer.final

## Rules
Проверить ответ на наличие слова disclaimer (case-insensitive).
Вычислить quality_score: 90 если есть disclaimer, 40 если нет.
Вернуть JSON с полями: contradictions_found (bool), quality_score (int), notes (string).

## Description
Четвёртый и финальный шаг pipeline. Контроль качества юридического ответа.
