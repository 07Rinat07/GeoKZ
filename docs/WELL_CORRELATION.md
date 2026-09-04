# GeoKZ — Well Correlation / Ұңғымалар қималарын корреляциялау / Корреляция разрезов

## RU

### Назначение
Модуль сопоставляет геологические разрезы опорной и соседних скважин. Он предназначен для визуального и текстового анализа положения реперов, литологии, коллекторов и флюидонасыщенных интервалов.

### Входные данные
- опорная скважина;
- соседние скважины;
- WellMarker: код репера, глубина, MD/TVD/TVDSS, источник, confidence, verification;
- WellInterval: top/base, local horizon, lithology, porosity, permeability, net pay, fluid, hydrocarbon status.

### Правила сопоставления
1. Для реперов предпочтителен TVDSS.
2. Если TVDSS отсутствует, допускается TVD или MD только при одинаковом depth reference.
3. Несовместимые depth references не соединяются автоматически.
4. Интервалы сопоставляются по нормализованному `local_horizon`.
5. Вычисляются различия thickness, net pay, porosity, permeability, lithology, fluid и hydrocarbon status.
6. Автоматическая корреляция является рабочей гипотезой и не заменяет экспертную интерпретацию.
7. Каждая отметка должна быть прослеживаема до источника/ГИС/документа.

### Визуализация
PySide6 viewer должен показывать вертикальные колонки скважин, реперы, линии корреляции, литологию, коллекторы, нефть/газ/воду и масштаб глубины. Выбор элемента открывает provenance и исходные данные.

## KK

### Мақсаты
Модуль тірек және көршілес ұңғымалардың геологиялық қималарын салыстырады. Реперлердің, литологияның, коллекторлардың және флюидке қаныққан интервалдардың орналасуын визуалды және мәтіндік түрде талдауға арналған.

### Салыстыру ережелері
1. Реперлер үшін TVDSS басым қолданылады.
2. TVDSS болмаса, TVD немесе MD тек бірдей depth reference кезінде салыстырылады.
3. Үйлеспейтін depth references автоматты түрде қосылмайды.
4. Интервалдар нормаланған `local_horizon` бойынша салыстырылады.
5. Thickness, net pay, porosity, permeability, lithology, fluid және hydrocarbon status айырмалары есептеледі.
6. Автоматты корреляция сараптамалық интерпретацияны алмастырмайды.
7. Әр белгі дереккөзге/ҰГЗ-ға/құжатқа дейін қадағалануы тиіс.

### Визуализация
PySide6 viewer ұңғыма бағандарын, реперлерді, корреляциялық сызықтарды, литологияны, коллекторларды, мұнай/газ/суды және тереңдік масштабын көрсетуі тиіс. Элементті таңдау provenance және бастапқы деректерді ашады.

## EN

### Purpose
The module compares geological sections of a reference well and nearby wells. It supports visual and textual analysis of markers, lithology, reservoirs and fluid-bearing intervals.

### Correlation rules
1. TVDSS is preferred for markers.
2. If TVDSS is unavailable, TVD or MD may be compared only when the depth reference is compatible.
3. Incompatible depth references are never connected automatically.
4. Intervals are matched by normalized `local_horizon`.
5. The engine compares thickness, net pay, porosity, permeability, lithology, fluid and hydrocarbon status.
6. Automatic correlation is a working hypothesis and does not replace expert interpretation.
7. Every marker and interval should be traceable to its source, well log or document.

### Visualization
The PySide6 viewer should render vertical well columns, markers, correlation lines, lithology, reservoirs, oil/gas/water intervals and a depth scale. Selecting an element opens provenance and source data.
