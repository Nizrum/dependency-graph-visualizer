# Инструмент командной строки для визуализации графа зависимостей

## Общее описание

Git Dependency Graph Visualizer — это инструмент для визуализации зависимостей между коммитами в Git-репозитории, включая их деревья (tree) и объекты (blob). Граф представлен в формате PlantUML, который может быть использован для создания диаграмм.

Программа позволяет:

1. Построить граф зависимостей, начиная с последнего коммита до указанной даты.

2. Включить в граф транзитивные зависимости: tree и blob объекты.

3. Сохранить граф в формате .puml для визуализации с помощью PlantUML.

4. Автоматически открыть сгенерированное изображение.

## Описание функций

1. parse_object - Извлекает информацию из git-объекта (коммит, дерево или файл). Возвращает словарь с данными объекта: тип объекта, хэш объекта, описание для визуализации, список дочерних объектов (для коммитов — родители, для деревьев — файлы).

2. parse_commit - Разбирает содержимое коммита для извлечения информации о деревьях, родителях, авторе, дате и сообщении. Возвращает словарь с данными коммита: хэш коммита, хэш дерева, список хэшей родителей, дата создания коммита, сообщение коммита.

3. parse_tree - Разбирает содержимое дерева Git для извлечения информации о файлах и поддеревьях. Возвращает список дочерних объектов дерева.

4. find_last_commit_before_date - Находит последний коммит, сделанный до указанной даты. Возвращает хэш коммита, который был сделан до указанной даты, или None, если такого коммита нет.

5. build_commit_graph - Строит граф зависимостей для указанного коммита и всех его зависимостей. Возвращает граф в виде словаря, содержащего узлы и зависимости.

6. generate_plantuml - Создаёт файл в формате PlantUML на основе графа зависимостей.

7. generate_graph_image - С помощью PlantUML генерирует изображение графа в формате PNG из файла .puml. Возвращает путь к сгенерированному изображению.

8. open_image - Открывает сгенерированное изображение в стандартной программе просмотра.

## Примеры использования

Для использования программы необходимо скачать PlantUML и убедиться, что у вас установлен Java.

1. Запуск программы с параметрами командной строки.

2. Сгенерированный файл graph.puml.

3. Сгенерированной изображение graph.png.

## Результаты тестирования

