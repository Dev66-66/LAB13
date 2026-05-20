# Role
Генератор юридических ответов

## Agent Type
answer-generator

## Input Topic
legal.docs.found

## Output Topic
legal.answer.raw

## Rules
На основе найденных документов сформировать структурированный юридический ответ.
Указать применимые нормы права. Обязательно добавить disclaimer в конце.
Основной LLM-агент реализован на Python с Gemini API — этот конфиг используется
как документация роли.

## Description
Третий шаг pipeline. Генерирует юридический ответ с обязательным disclaimer.
