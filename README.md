# PULSECARE BACKEND

Este es el repositorio del backend de PulseCare, una aplicación diseñada para monitorear y mejorar la salud cardiovascular de los usuarios. El backend está construido utilizando FastAPI, TensorFlow, y otras tecnologías para alojar la capa de inteligencia artificial y gestionar las operaciones del servidor.

## Modelo de Datos

Tablas:

- **users**: Almacena información de los usuarios.
  Columnas:
  - id: Identificador único del usuario.
  - id_role: Clave foránea que referencia al rol del usuario en la tabla roles
  - email: Correo electrónico del usuario, único y requerido.
  - hashed_password: Contraseña hasheada del usuario, requerida.
  - is_active: Indica si la cuenta del usuario está activa, por defecto es True.
  - created_at: Timestamp de creación del usuario, con zona horaria UTC.

  Relaciones:
  - wellbeing_entries: Relación uno a muchos con la tabla wellbeing_entries, que almacena los registros diarios de bienestar del usuario.
  - role: Relación con la tabla roles, que permite acceder a los datos del rol del usuario.

- **roles**: Define los roles de usuario, como "estudiante" y "administrador", con sus respectivos permisos.
  Columnas:
  - id: Identificador único del rol.
  - name: Nombre del rol, único y requerido (e.g. "Estudiante", "Admin").

  Relaciones:
  - users: Relación con la tabla users, que permite acceder a los usuarios que tienen este rol.

- **wellbeing_entries**: Registra el bienestar diario de los usuarios, con campos como estado de ánimo, horas de sueño, carga académica percibida, nivel de energía o fatiga, regularidad de registro, cambios recientes respecto al promedio personal, tendencia de los últimos 7 días, y tendencia de los últimos 14 días.
  Columnas:
  - id: Identificador único del registro de bienestar.
  - user_id: Clave foránea que referencia al usuario que hizo el registro.
  - mood: Estado de ánimo diario, en una escala de 1 a 10.
  - sleep_hours: Horas de sueño la noche anterior, como número decimal.
  - academic_load: Carga académica percibida, en una escala de 1 a 10.
  - energy_level: Nivel de energía o fatiga, en una escala de 1 a 10.
  - regularity_score: Regularidad de registro, calculada como el porcentaje de días registrados en los últimos 30 días.
  - recent_change: Cambios recientes respecto al promedio personal, calculados como la diferencia entre el valor actual y el promedio de los últimos 30 días para cada variable.
  - trend_7d: Tendencia de los últimos 7 días, calculada como la pendiente de la regresión lineal sobre los valores de los últimos 7 días para cada variable.
  - trend_14d: Tendencia de los últimos 14 días, calculada como la pendiente de la regresión lineal sobre los valores de los últimos 14 días para cada variable.
  - is_synthetic: Indica si el registro fue generado por un script de prueba o corresponde a datos reales.
  - created_at: Timestamp de creación del registro, con zona horaria UTC.

  Relaciones:
  - user: Relación con la tabla users, que permite acceder a los datos del usuario que hizo el registro.
  - model_input_snapshot: Relación uno a uno con la tabla model_input_snapshots, que almacena la representación de entrada derivada para la capa de IA.
  - risk_label: Relación uno a uno con la tabla risk_labels, que almacena la etiqueta de riesgo utilizada como ground truth para el entrenamiento supervisado del modelo de IA.

- **model_input_snapshots**: Guarda las representaciones de entrada derivadas para la capa de IA, vinculadas a los registros de bienestar diarios.
  Columnas:
  - id: Identificador único de la representación de entrada.
  - entry_id: Clave foránea que referencia al registro de bienestar diario, con relación uno a uno.
  - input_vector: Vector de entrada serializado (e.g. JSON o binario) listo para ser consumido por el modelo de IA.
  - created_at: Timestamp de creación de la representación de entrada, con zona horaria UTC.

  Relaciones:
  - wellbeing_entry: Relación con la tabla wellbeing_entries, que permite acceder al registro de bienestar asociado a esta representación de entrada.

- **risk_labels**: Contiene las etiquetas de riesgo utilizadas como ground truth para el entrenamiento supervisado del modelo de IA, asociadas a los registros de bienestar diarios.
  Columnas:
  - id: Identificador único de la etiqueta de riesgo.
  - entry_id: Clave foránea que referencia al registro de bienestar diario, con relación uno a uno.
  - risk_level: Nivel de riesgo, en una escala de 1 a 10.
  - label_source: Fuente de la etiqueta de riesgo, e.g. "manual", "modelo_v1", "modelo_v2".
  - label_note: Nota adicional sobre la etiqueta de riesgo, opcional.
  - created_at: Timestamp de creación de la etiqueta de riesgo, con zona horaria UTC.

  Relaciones:
  - wellbeing_entry: Relación con la tabla wellbeing_entries, que permite acceder al registro de bienestar asociado a esta etiqueta de riesgo.

- **training_runs**: Registra las ejecuciones de entrenamiento del modelo de IA, incluyendo la fecha, los parámetros utilizados, las métricas obtenidas y la ubicación del modelo serializado.
  Columnas:
  - id: Identificador único de la ejecución de entrenamiento.
  - run_date: Fecha y hora de la ejecución del entrenamiento, con zona horaria UTC.
  - parameters: Parámetros utilizados para el entrenamiento, almacenados como JSON.
  - metrics: Métricas obtenidas del entrenamiento, almacenadas como JSON (e.g. accuracy, precision, recall).
  - model_path: Ruta o URL donde se encuentra el modelo serializado resultante del entrenamiento.

  Relaciones:
  - No tiene relaciones directas con otras tablas, pero puede ser consultada para obtener información sobre las ejecuciones de entrenamiento realizadas.

## Endpoints

### Estado general

| Método | Ruta                     | Descripción                                                             | Acceso  |
| ------ | ------------------------ | ----------------------------------------------------------------------- | ------- |
| GET    | `/`                      | Verifica que el servicio esté activo.                                   | Público |
| GET    | `/health`                | Healthcheck de la API.                                                  | Público |
| GET    | `/insert-initial-data`   | Inserta roles iniciales (`Estudiante`, `Admin`) si la tabla está vacía. | Público |
| GET    | `/manage-synthetic-data` | Inserta o elimina datos sintéticos para pruebas.                        | Público |
| GET    | `/seed-synthetic-data`   | Inserta datos sintéticos para pruebas.                                  | Público |
| GET    | `/delete-synthetic-data` | Elimina los datos sintéticos insertados.                                | Público |

### Autenticación

| Método | Ruta             | Descripción                                              | Acceso                                   |
| ------ | ---------------- | -------------------------------------------------------- | ---------------------------------------- |
| POST   | `/auth/register` | Crea un usuario nuevo con `email` y contraseña hasheada. | Público                                  |
| POST   | `/auth/login`    | Genera un token JWT para un usuario válido.              | Público                                  |
| GET    | `/auth/me`       | Devuelve el usuario autenticado a partir del token.      | Requiere `Authorization: Bearer <token>` |

#### `POST /auth/register`

Registra un usuario nuevo.

Request body:

```json
{
  "email": "estudiante@unisimon.com.co",
  "password": "MiClaveSegura123"
}
```

Respuestas:

- `201 Created`: usuario creado correctamente.
- `409 Conflict`: el correo ya existe.
- `400 Bad Request`: datos inválidos.

#### `POST /auth/login`

Autentica al usuario y devuelve un token JWT.

Request body:

```json
{
  "email": "estudiante@unisimon.com.co",
  "password": "MiClaveSegura123"
}
```

Response:

```json
{
  "access_token": "token.jwt.aqui",
  "token_type": "bearer"
}
```

Respuestas:

- `200 OK`: credenciales válidas.
- `401 Unauthorized`: correo o contraseña incorrectos.
- `400 Bad Request`: datos inválidos.

#### `GET /auth/me`

Devuelve el usuario autenticado.

Headers:

```http
Authorization: Bearer <token>
```

Respuestas:

- `200 OK`: datos del usuario autenticado.
- `401 Unauthorized`: token ausente o inválido.

### Bienestar diario

| Método | Ruta                                            | Descripción                                                               | Acceso         |
| ------ | ----------------------------------------------- | ------------------------------------------------------------------------- | -------------- |
| POST   | `/api/wellbeing/entries`                        | Registra un autorregistro diario de bienestar.                            | Requiere token |
| GET    | `/api/wellbeing/entries/{entry_id}`             | Consulta un registro diario propio.                                       | Requiere token |
| POST   | `/api/wellbeing/entries/{entry_id}/model-input` | Genera y guarda la representación de entrada para IA.                     | Requiere token |
| POST   | `/api/wellbeing/entries/{entry_id}/label`       | Guarda la etiqueta de riesgo ground truth para entrenamiento supervisado. | Requiere token |

#### `POST /api/wellbeing/entries`

Registra el estado de bienestar diario del estudiante.

Request body:

```json
{
  "mood_score": 4,
  "sleep_hours": 7.5,
  "academic_load": 4,
  "energy_fatigue": 3,
  "registration_regular": 5,
  "recent_change_vs_average": -1.2,
  "trend_7d": -0.8,
  "trend_14d": -1.1
}
```

Respuestas:

- `201 Created`: registro creado correctamente.
- `400 Bad Request`: validación fallida.
- `401 Unauthorized`: token ausente o inválido.

#### `GET /api/wellbeing/entries/{entry_id}`

Devuelve un registro de bienestar del usuario autenticado.

Respuestas:

- `200 OK`: registro encontrado.
- `404 Not Found`: el registro no existe.
- `401 Unauthorized`: token ausente o inválido.

#### `POST /api/wellbeing/entries/{entry_id}/model-input`

Genera la representación de entrada derivada para el modelo.

Respuestas:

- `201 Created`: snapshot creado o reutilizado.
- `404 Not Found`: el registro no existe.
- `401 Unauthorized`: token ausente o inválido.

#### `POST /api/wellbeing/entries/{entry_id}/label`

Registra la etiqueta de riesgo usada como ground truth.

Request body:

```json
{
  "risk_level": 2,
  "label_source": "manual",
  "label_note": "PHQ-9 alto y validación por bienestar"
}
```

Respuestas:

- `201 Created`: etiqueta guardada correctamente.
- `400 Bad Request`: datos inválidos o etiqueta no guardable.
- `404 Not Found`: el registro no existe.

### Inteligencia artificial

| Método | Ruta                         | Descripción                                                       | Acceso         |
| ------ | ---------------------------- | ----------------------------------------------------------------- | -------------- |
| POST   | `/api/ai/train`              | Entrena el modelo de forma inmediata y devuelve métricas.         | Solo Admin     |
| POST   | `/api/ai/train/async`        | Lanza el entrenamiento en segundo plano y crea un `training_run`. | Solo Admin     |
| GET    | `/api/ai/train/{run_id}`     | Consulta el estado y métricas de una ejecución de entrenamiento.  | Solo Admin     |
| GET    | `/api/ai/predict/{entry_id}` | Ejecuta la predicción para un registro de bienestar.              | Requiere token |
| POST   | `/api/ai/predict/{entry_id}` | Ejecuta la predicción para un registro de bienestar.              | Requiere token |
| GET    | `/api/ai/artifact`           | Inspecciona el artefacto del modelo y el último reporte guardado. | Solo Admin     |

#### `POST /api/ai/train`

Entrena el clasificador supervisado con los datos etiquetados disponibles.

Respuestas:

- `200 OK`: entrenamiento finalizado y métricas devueltas.
- `403 Forbidden`: el usuario no tiene rol Admin.
- `400 Bad Request`: no hay suficientes datos etiquetados.

#### `POST /api/ai/train/async`

Inicia el entrenamiento en background y registra el proceso en `training_runs`.

Respuestas:

- `202 Accepted`: entrenamiento en cola.
- `403 Forbidden`: el usuario no tiene rol Admin.

#### `GET /api/ai/train/{run_id}`

Devuelve el estado de una ejecución de entrenamiento.

Respuestas:

- `200 OK`: información del run.
- `403 Forbidden`: el usuario no tiene rol Admin.
- `404 Not Found`: el entrenamiento no existe.

#### `GET /api/ai/predict/{entry_id}` y `POST /api/ai/predict/{entry_id}`

Generan la predicción del nivel de riesgo para un registro de bienestar.

Respuestas:

- `200 OK`: predicción generada.
- `403 Forbidden`: el usuario no es propietario del registro ni Admin.
- `404 Not Found`: el registro no existe o no existe el modelo entrenado.

#### `GET /api/ai/artifact`

Devuelve metadatos del archivo del modelo y del último entrenamiento guardado.

Respuestas:

- `200 OK`: artefacto encontrado o ausente con metadatos del último run.
- `403 Forbidden`: el usuario no tiene rol Admin.

### Notas de uso

- Los endpoints protegidos requieren el header `Authorization: Bearer <token>`.
- El rol `Admin` corresponde a `id_role = 2`.
- Antes de entrenar el modelo, deben existir `risk_labels` y `model_input_snapshots` asociados a los registros de bienestar.

## Scripts útiles

### `scripts/seed_synthetic_data.py`

Inserta datos sintéticos de bienestar, snapshots de entrada y etiquetas de riesgo para pruebas o entrenamiento inicial.

Ejemplo:

```bash
python scripts/seed_synthetic_data.py --count 90 --seed 42
```

Opciones útiles:

- `--count`: cantidad de registros sintéticos a generar.
- `--seed`: semilla para reproducibilidad.
- `--email`: correo del usuario sintético a reutilizar o crear.

### `scripts/delete_synthetic_data.py`

Elimina todos los registros marcados como sintéticos y limpia sus relaciones dependientes.

Ejemplo:

```bash
python scripts/delete_synthetic_data.py
```

Ambos scripts usan la columna `is_synthetic` de `wellbeing_entries` para separar datos reales de datos generados.
