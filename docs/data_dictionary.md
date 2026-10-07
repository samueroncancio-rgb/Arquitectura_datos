# Diccionario de Datos: Superstore Sales Dataset

Este documento detalla la estructura, tipos, características estadísticas y consideraciones de calidad del dataset real **Superstore Sales** tras la inspección exploratoria de los datos crudos.

---

## 1. Resumen General del Dataset

- **Archivo fuente inspeccionado:** `data/raw/superstore.csv` (originalmente `Sample - Superstore.csv`)
- **Total de Filas (registros):** 9,994
- **Total de Columnas:** 21
- **Codificación observada:** UTF-8 / Windows-1252
- **Rango temporal de órdenes:** 2014-01-03 a 2017-12-30 (4 años de transacciones comerciales)
- **Registros completamente duplicados:** 0 filas
- **Valores nulos totales:** 0 en todas las columnas

---

## 2. Diccionario de Datos

| Columna | Tipo de Dato | Significado | Nullable | Cardinalidad (Únicos) | Valores de Muestra / Rango |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Row ID** | `integer` | Identificador único secuencial de la línea de pedido | No | 9,994 | `1, 2, 3, ...` |
| **Order ID** | `string` | Identificador de la orden de compra (puede agrupar varios ítems) | No | 5,009 | `CA-2016-152156`, `US-2015-108966` |
| **Order Date** | `date` (`M/D/YYYY`) | Fecha en que el cliente realizó el pedido | No | 1,237 | `11/8/2016` (2014 a 2017) |
| **Ship Date** | `date` (`M/D/YYYY`) | Fecha en que el pedido fue despachado/enviado | No | 1,334 | `11/11/2016` (posterior o igual a Order Date) |
| **Ship Mode** | `string` | Método/clase de envío logístico | No | 4 | `Standard Class`, `Second Class`, `First Class`, `Same Day` |
| **Customer ID** | `string` | Identificador único del cliente | No | 793 | `CG-12520`, `DV-13045` |
| **Customer Name**| `string` | Nombre completo del cliente | No | 793 | `Claire Gute`, `Darrin Van Huff` |
| **Segment** | `string` | Segmento de mercado del cliente | No | 3 | `Consumer`, `Corporate`, `Home Office` |
| **Country** | `string` | País donde se realizó la transacción | No | 1 | `United States` |
| **City** | `string` | Ciudad de destino del pedido | No | 531 | `New York City`, `Los Angeles`, `Henderson` |
| **State** | `string` | Estado federado de destino | No | 49 | `California`, `New York`, `Texas`, `Kentucky` |
| **Postal Code** | `string` / `int` | Código postal estadounidense | No | 631 | `42420`, `90036`, `01841` |
| **Region** | `string` | Región geográfica de ventas | No | 4 | `South`, `West`, `Central`, `East` |
| **Product ID** | `string` | Código identificador del producto comercializado | No | 1,862 | `FUR-BO-10001798`, `OFF-LA-10000240` |
| **Category** | `string` | Categoría principal del catálogo de productos | No | 3 | `Furniture`, `Office Supplies`, `Technology` |
| **Sub-Category** | `string` | Subcategoría específica del producto | No | 17 | `Bookcases`, `Chairs`, `Binders`, `Copiers`, etc. |
| **Product Name** | `string` | Descripción / nombre comercial del producto | No | 1,850 | `Bush Somerset Collection Bookcase` |
| **Sales** | `decimal` | Importe bruto de ventas de la línea de pedido ($ USD) | No | 5,825 | Min: $0.444 | Media: $229.86 | Max: $22,638.48 |
| **Quantity** | `integer` | Número de unidades adquiridas en la línea de pedido | No | 14 | Min: 1 | Media: 3.79 | Max: 14 |
| **Discount** | `decimal` | Tasa de descuento aplicada (de 0.00 a 0.80) | No | 12 | Min: 0.00 (0%) | Media: 0.16 | Max: 0.80 (80%) |
| **Profit** | `decimal` | Beneficio neto o margen en dólares de la línea de pedido | No | 7,287 | Min: -$6,599.98 | Media: $28.66 | Max: $8,399.98 |

---

## 3. Relaciones y Llaves del Dataset

1. **Granularidad:** 
   - Cada fila representa un **ítem de línea de pedido individual** (`line item`).
   - La clave primaria natural de la fila es `Row ID`.
2. **Relación Orden - Ítem:**
   - Hay 5,009 `Order ID` únicos repartidos en 9,994 filas (en promedio ~2 ítems por orden).
   - Existen 8 casos donde un mismo `Order ID` tiene dos entradas con el mismo `Product ID`, confirmando que la unicidad estricta reside en `Row ID` y no en `(Order ID, Product ID)`.
3. **Consistencia Dimensional:**
   - **Clientes (`Customer ID`):** 793 IDs únicos corresponden exactamente a 793 nombres únicos. Cada cliente pertenece consistentemente a un único `Segment`.
   - **Productos (`Product ID`):** Hay 1,862 IDs únicos y 1,850 nombres únicos (32 productos tienen variaciones textuales mínimas en el nombre registradas a lo largo de los 4 años).
   - **Fechas:** Para el 100% de los registros, `Ship Date >= Order Date`. El tiempo promedio de despacho es de 3.96 días.

---

## 4. Hallazgos y Reglas de Calidad para el Pipeline

1. **Formato de Fechas:** Las fechas originales vienen en formato `M/D/YYYY`. En la capa Staging se estandarizan a formato ISO `YYYY-MM-DD` (`DATE`).
2. **Nombres de Columnas:** Las columnas crudas contienen espacios (`Order ID`, `Ship Mode`). En Staging se transforman a `snake_case` (`order_id`, `ship_mode`).
3. **Márgenes Negativos:** La columna `Profit` contiene valores negativos (hasta -$6,599.98). Esto no es un error de datos sino una realidad comercial (pedidos con descuentos elevados de hasta 80% que generan pérdidas operativas).
4. **Códigos Postales:** Vienen en formato numérico (e.g. `42420`). Algunos códigos postales de la Costa Este de EE.UU. inician con cero (`01841`), por lo que en staging se deben tratar como texto (`VARCHAR(10)`).
