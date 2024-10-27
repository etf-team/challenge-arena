Бэкенд challenge arena (сокращенно CHAR)

https://etf-team.ru/api
https://etf-team.ru/api/docs
https://etf-team.ru/api/admin

Компоуз файл сам говорит за то, какие основные архитектурные 
компоненты содержит ПО.

Кратко поясню за самую объёмную часть -- python пакеты,
которые служат исходниками для запуска rest-api, daemon, 
run-migrations.

Кодовая база проекта в основном питон.  Она разбита на два
основных пакета
1. char_core (challenge arena core)
2. char_rest_api (...)

В первом сложная бизнес-логика, которая местами протекает
и во второй, потому-что время ограничено.  Но в целом такое
разделение было бы полезно для дальнейшего рефаторинга и
написания юниттестов (в пакете с доменной логикой даже есть
один тестик на 200+ строк).

Пожалуй, душноты проекту добавляет использование отдельного
DI фреймворка вместо того чтобы юзать дефолтные fastapi dependencies.
Однако это даже сейчас хорошо показало себя в тестах и в daemon --
написанные провайдеры зависимостей легко там переиспользовались.

Я в прошлом хакатоне писал код почище (+- по канонам начального DDD),
но это не принесло какого-то профита, только потерю времени -- 
реальзовал значительно меньше фич чем сейчас.  Поэтому было 
принято решение повысить размазывание слоёв.  В целом мне даже
немного понравилось.  Только смущает дублирование кода 
обеспечевающего безопасность (в сумме с тем, что тестов на 
безопасность нету.)

Был ещё вариант написать на джанге, понимаю что она во многих моментах
хорша для прототипирования.  Но (1) у уменя в ней мало опыта, (2) 
есть личные причины.