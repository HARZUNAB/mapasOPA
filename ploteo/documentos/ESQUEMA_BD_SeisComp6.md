# Esquema de la base de datos SeisComp6

_Documento de referencia. Generado el 07/09/2026._

## Regla rectora

Toda la documentación parte de la **solución preferida**: la que apunta `event.m_preferredoriginid`. Es la solución que un analista procesa (y la que NewPT usa y valida). Un evento puede tener varios orígenes (ver `originreference`), pero este documento describe la cadena preferida.

## Cadena de la solución preferida (resumen)

```
event
 └─ m_preferredoriginid ──────► ORIGEN PREFERIDO (origin)
      ├─ (sus) arrival [_parent_oid] ─► pick usado (m_pickid)
      │     └─ pick.m_waveformid_stationcode/networkcode ─► QUÉ ESTACIÓN (station/network)
      ├─ (sus) amplitude [_parent_oid] ─► stationmagnitude (m_originid = este origin)
      └─ (sus) dataused / reading
event
 ├─ m_preferredmagnitudeid ──► magnitude (magnitud preferida)
 └─ eventdescription (m_type='region name') ─► nombre de la región
```

## Leyenda de tipos

- Todas las tablas de objetos tienen `_oid` (identidad, referencia a `object._oid`) y `_parent_oid` (pertenencia al padre).
- Los enlaces entre objetos se hacen por **coincidencia de `_oid`** o por **`m_publicid`/`m_*id`** (texto) — no siempre hay llave foránea declarada.

## BASE

### object

Raíz común de todos los objetos del sistema.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_timestamp` | timestamp without time zone |

**Índices:**

- `object_pkey` → `ÚNICO object_pkey ON public.object USING btree (_oid)`

### publicobject

Traduce `_oid` ↔ ID público.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `m_publicid` | character varying |

**Índices:**

- `publicobject_m_publicid_key` → `ÚNICO publicobject_m_publicid_key ON public.publicobject USING btree (m_publicid)`
- `publicobject_pkey` → `ÚNICO publicobject_pkey ON public.publicobject USING btree (_oid)`

## NÚCLEO SÍSMICO

### event

El sismo agregado, tal como lo ve el analista.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_preferredoriginid` | character varying |
| `m_preferredmagnitudeid` | character varying |
| `m_preferredfocalmechanismid` | character varying |
| `m_type` | character varying |
| `m_typecertainty` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

**Índices:**

- `event__parent_oid` → `event__parent_oid ON public.event USING btree (_parent_oid)`
- `event_m_preferredfocalmechanismid` → `event_m_preferredfocalmechanismid ON public.event USING btree (m_preferredfocalmechanismid)`
- `event_m_preferredmagnitudeid` → `event_m_preferredmagnitudeid ON public.event USING btree (m_preferredmagnitudeid)`
- `event_m_preferredoriginid` → `event_m_preferredoriginid ON public.event USING btree (m_preferredoriginid)`
- `event_pkey` → `ÚNICO event_pkey ON public.event USING btree (_oid)`

_Enlaza la cadena preferida:_ `m_preferredoriginid`, `m_preferredmagnitudeid`

### origin

Una solución de hipocentro (un "origen").

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_time_value` | timestamp without time zone |
| `m_time_value_ms` | integer |
| `m_time_uncertainty` | double precision |
| `m_time_loweruncertainty` | double precision |
| `m_time_upperuncertainty` | double precision |
| `m_time_confidencelevel` | double precision |
| `m_time_pdf_variable_content` | bytea |
| `m_time_pdf_probability_content` | bytea |
| `m_time_pdf_used` | boolean |
| `m_latitude_value` | double precision |
| `m_latitude_uncertainty` | double precision |
| `m_latitude_loweruncertainty` | double precision |
| `m_latitude_upperuncertainty` | double precision |
| `m_latitude_confidencelevel` | double precision |
| `m_latitude_pdf_variable_content` | bytea |
| `m_latitude_pdf_probability_content` | bytea |
| `m_latitude_pdf_used` | boolean |
| `m_longitude_value` | double precision |
| `m_longitude_uncertainty` | double precision |
| `m_longitude_loweruncertainty` | double precision |
| `m_longitude_upperuncertainty` | double precision |
| `m_longitude_confidencelevel` | double precision |
| `m_longitude_pdf_variable_content` | bytea |
| `m_longitude_pdf_probability_content` | bytea |
| `m_longitude_pdf_used` | boolean |
| `m_depth_value` | double precision |
| `m_depth_uncertainty` | double precision |
| `m_depth_loweruncertainty` | double precision |
| `m_depth_upperuncertainty` | double precision |
| `m_depth_confidencelevel` | double precision |
| `m_depth_pdf_variable_content` | bytea |
| `m_depth_pdf_probability_content` | bytea |
| `m_depth_pdf_used` | boolean |
| `m_depth_used` | boolean |
| `m_depthtype` | character varying |
| `m_timefixed` | boolean |
| `m_epicenterfixed` | boolean |
| `m_referencesystemid` | character varying |
| `m_methodid` | character varying |
| `m_earthmodelid` | character varying |
| `m_quality_associatedphasecount` | integer |
| `m_quality_usedphasecount` | integer |
| `m_quality_associatedstationcount` | integer |
| `m_quality_usedstationcount` | integer |
| `m_quality_depthphasecount` | integer |
| `m_quality_standarderror` | double precision |
| `m_quality_azimuthalgap` | double precision |
| `m_quality_secondaryazimuthalgap` | double precision |
| `m_quality_groundtruthlevel` | character varying |
| `m_quality_maximumdistance` | double precision |
| `m_quality_minimumdistance` | double precision |
| `m_quality_mediandistance` | double precision |
| `m_quality_used` | boolean |
| `m_uncertainty_horizontaluncertainty` | double precision |
| `m_uncertainty_minhorizontaluncertainty` | double precision |
| `m_uncertainty_maxhorizontaluncertainty` | double precision |
| `m_uncertainty_azimuthmaxhorizontaluncertainty` | double precision |
| `m_uncertainty_confidenceellipsoid_semimajoraxislength` | double precision |
| `m_uncertainty_confidenceellipsoid_semiminoraxislength` | double precision |
| `m_uncertainty_confidenceellipsoid_semiintermediateaxislength` | double precision |
| `m_uncertainty_confidenceellipsoid_majoraxisplunge` | double precision |
| `m_uncertainty_confidenceellipsoid_majoraxisazimuth` | double precision |
| `m_uncertainty_confidenceellipsoid_majoraxisrotation` | double precision |
| `m_uncertainty_confidenceellipsoid_used` | boolean |
| `m_uncertainty_preferreddescription` | character varying |
| `m_uncertainty_confidencelevel` | double precision |
| `m_uncertainty_used` | boolean |
| `m_type` | character varying |
| `m_evaluationmode` | character varying |
| `m_evaluationstatus` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

**Índices:**

- `origin__parent_oid` → `origin__parent_oid ON public.origin USING btree (_parent_oid)`
- `origin_m_time_value_m_time_value_ms` → `origin_m_time_value_m_time_value_ms ON public.origin USING btree (m_time_value, m_time_value_ms)`
- `origin_pkey` → `ÚNICO origin_pkey ON public.origin USING btree (_oid)`

### magnitude

La magnitud del evento.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_magnitude_value` | double precision |
| `m_magnitude_uncertainty` | double precision |
| `m_magnitude_loweruncertainty` | double precision |
| `m_magnitude_upperuncertainty` | double precision |
| `m_magnitude_confidencelevel` | double precision |
| `m_magnitude_pdf_variable_content` | bytea |
| `m_magnitude_pdf_probability_content` | bytea |
| `m_magnitude_pdf_used` | boolean |
| `m_type` | character varying |
| `m_originid` | character varying |
| `m_methodid` | character varying |
| `m_stationcount` | integer |
| `m_azimuthalgap` | double precision |
| `m_evaluationstatus` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

**Índices:**

- `magnitude__parent_oid` → `magnitude__parent_oid ON public.magnitude USING btree (_parent_oid)`
- `magnitude_pkey` → `ÚNICO magnitude_pkey ON public.magnitude USING btree (_oid)`

_Enlaza la cadena preferida:_ `m_originid`

### eventdescription

Textos descriptivos del evento.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_text` | character varying |
| `m_type` | character varying |

**Índices:**

- `eventdescription__parent_oid` → `eventdescription__parent_oid ON public.eventdescription USING btree (_parent_oid)`
- `eventdescription_composite_index` → `ÚNICO eventdescription_composite_index ON public.eventdescription USING btree (_parent_oid, m_type)`
- `eventdescription_pkey` → `ÚNICO eventdescription_pkey ON public.eventdescription USING btree (_oid)`

### originreference

Enlace evento ↔ origen (contexto).

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_originid` | character varying |

**Índices:**

- `originreference__parent_oid` → `originreference__parent_oid ON public.originreference USING btree (_parent_oid)`
- `originreference_composite_index` → `ÚNICO originreference_composite_index ON public.originreference USING btree (_parent_oid, m_originid)`
- `originreference_m_originid` → `originreference_m_originid ON public.originreference USING btree (m_originid)`
- `originreference_pkey` → `ÚNICO originreference_pkey ON public.originreference USING btree (_oid)`

_Enlaza la cadena preferida:_ `m_originid`

## CADENA DEL ORIGEN PREFERIDO

### arrival

Llegada de una fase usada en la localización.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_pickid` | character varying |
| `m_phase_code` | character varying |
| `m_timecorrection` | double precision |
| `m_azimuth` | double precision |
| `m_distance` | double precision |
| `m_takeoffangle` | double precision |
| `m_timeresidual` | double precision |
| `m_horizontalslownessresidual` | double precision |
| `m_backazimuthresidual` | double precision |
| `m_timeused` | boolean |
| `m_horizontalslownessused` | boolean |
| `m_backazimuthused` | boolean |
| `m_weight` | double precision |
| `m_earthmodelid` | character varying |
| `m_preliminary` | boolean |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

**Índices:**

- `arrival__parent_oid` → `arrival__parent_oid ON public.arrival USING btree (_parent_oid)`
- `arrival_composite_index` → `ÚNICO arrival_composite_index ON public.arrival USING btree (_parent_oid, m_pickid)`
- `arrival_m_pickid` → `arrival_m_pickid ON public.arrival USING btree (m_pickid)`
- `arrival_pkey` → `ÚNICO arrival_pkey ON public.arrival USING btree (_oid)`

_Enlaza la cadena preferida:_ `m_pickid`

### pick

Detección de una fase en un canal (tiene hora y canal).

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_time_value` | timestamp without time zone |
| `m_time_value_ms` | integer |
| `m_time_uncertainty` | double precision |
| `m_time_loweruncertainty` | double precision |
| `m_time_upperuncertainty` | double precision |
| `m_time_confidencelevel` | double precision |
| `m_time_pdf_variable_content` | bytea |
| `m_time_pdf_probability_content` | bytea |
| `m_time_pdf_used` | boolean |
| `m_waveformid_networkcode` | character varying |
| `m_waveformid_stationcode` | character varying |
| `m_waveformid_locationcode` | character varying |
| `m_waveformid_channelcode` | character varying |
| `m_waveformid_resourceuri` | character varying |
| `m_filterid` | character varying |
| `m_methodid` | character varying |
| `m_horizontalslowness_value` | double precision |
| `m_horizontalslowness_uncertainty` | double precision |
| `m_horizontalslowness_loweruncertainty` | double precision |
| `m_horizontalslowness_upperuncertainty` | double precision |
| `m_horizontalslowness_confidencelevel` | double precision |
| `m_horizontalslowness_pdf_variable_content` | bytea |
| `m_horizontalslowness_pdf_probability_content` | bytea |
| `m_horizontalslowness_pdf_used` | boolean |
| `m_horizontalslowness_used` | boolean |
| `m_backazimuth_value` | double precision |
| `m_backazimuth_uncertainty` | double precision |
| `m_backazimuth_loweruncertainty` | double precision |
| `m_backazimuth_upperuncertainty` | double precision |
| `m_backazimuth_confidencelevel` | double precision |
| `m_backazimuth_pdf_variable_content` | bytea |
| `m_backazimuth_pdf_probability_content` | bytea |
| `m_backazimuth_pdf_used` | boolean |
| `m_backazimuth_used` | boolean |
| `m_slownessmethodid` | character varying |
| `m_onset` | character varying |
| `m_phasehint_code` | character varying |
| `m_phasehint_used` | boolean |
| `m_polarity` | character varying |
| `m_evaluationmode` | character varying |
| `m_evaluationstatus` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

**Índices:**

- `pick__parent_oid` → `pick__parent_oid ON public.pick USING btree (_parent_oid)`
- `pick_m_time_value_m_time_value_ms` → `pick_m_time_value_m_time_value_ms ON public.pick USING btree (m_time_value, m_time_value_ms)`
- `pick_pkey` → `ÚNICO pick_pkey ON public.pick USING btree (_oid)`

_Enlaza la cadena preferida:_ `m_waveformid_networkcode`, `m_waveformid_stationcode`

### amplitude

Amplitud medida sobre una señal.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_type` | character varying |
| `m_amplitude_value` | double precision |
| `m_amplitude_uncertainty` | double precision |
| `m_amplitude_loweruncertainty` | double precision |
| `m_amplitude_upperuncertainty` | double precision |
| `m_amplitude_confidencelevel` | double precision |
| `m_amplitude_pdf_variable_content` | bytea |
| `m_amplitude_pdf_probability_content` | bytea |
| `m_amplitude_pdf_used` | boolean |
| `m_amplitude_used` | boolean |
| `m_timewindow_reference` | timestamp without time zone |
| `m_timewindow_reference_ms` | integer |
| `m_timewindow_begin` | double precision |
| `m_timewindow_end` | double precision |
| `m_timewindow_used` | boolean |
| `m_period_value` | double precision |
| `m_period_uncertainty` | double precision |
| `m_period_loweruncertainty` | double precision |
| `m_period_upperuncertainty` | double precision |
| `m_period_confidencelevel` | double precision |
| `m_period_pdf_variable_content` | bytea |
| `m_period_pdf_probability_content` | bytea |
| `m_period_pdf_used` | boolean |
| `m_period_used` | boolean |
| `m_snr` | double precision |
| `m_unit` | character varying |
| `m_pickid` | character varying |
| `m_waveformid_networkcode` | character varying |
| `m_waveformid_stationcode` | character varying |
| `m_waveformid_locationcode` | character varying |
| `m_waveformid_channelcode` | character varying |
| `m_waveformid_resourceuri` | character varying |
| `m_waveformid_used` | boolean |
| `m_filterid` | character varying |
| `m_methodid` | character varying |
| `m_scalingtime_value` | timestamp without time zone |
| `m_scalingtime_value_ms` | integer |
| `m_scalingtime_uncertainty` | double precision |
| `m_scalingtime_loweruncertainty` | double precision |
| `m_scalingtime_upperuncertainty` | double precision |
| `m_scalingtime_confidencelevel` | double precision |
| `m_scalingtime_pdf_variable_content` | bytea |
| `m_scalingtime_pdf_probability_content` | bytea |
| `m_scalingtime_pdf_used` | boolean |
| `m_scalingtime_used` | boolean |
| `m_magnitudehint` | character varying |
| `m_evaluationmode` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

**Índices:**

- `amplitude__parent_oid` → `amplitude__parent_oid ON public.amplitude USING btree (_parent_oid)`
- `amplitude_m_pickid` → `amplitude_m_pickid ON public.amplitude USING btree (m_pickid)`
- `amplitude_pkey` → `ÚNICO amplitude_pkey ON public.amplitude USING btree (_oid)`
- `amplitude_timewindow_reference` → `amplitude_timewindow_reference ON public.amplitude USING btree (m_timewindow_reference, m_timewindow_reference_ms)`

_Enlaza la cadena preferida:_ `m_pickid`, `m_waveformid_networkcode`, `m_waveformid_stationcode`

### stationmagnitude

Magnitud calculada por estación.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_originid` | character varying |
| `m_magnitude_value` | double precision |
| `m_magnitude_uncertainty` | double precision |
| `m_magnitude_loweruncertainty` | double precision |
| `m_magnitude_upperuncertainty` | double precision |
| `m_magnitude_confidencelevel` | double precision |
| `m_magnitude_pdf_variable_content` | bytea |
| `m_magnitude_pdf_probability_content` | bytea |
| `m_magnitude_pdf_used` | boolean |
| `m_type` | character varying |
| `m_amplitudeid` | character varying |
| `m_methodid` | character varying |
| `m_waveformid_networkcode` | character varying |
| `m_waveformid_stationcode` | character varying |
| `m_waveformid_locationcode` | character varying |
| `m_waveformid_channelcode` | character varying |
| `m_waveformid_resourceuri` | character varying |
| `m_waveformid_used` | boolean |
| `m_passedqc` | boolean |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

**Índices:**

- `stationmagnitude__parent_oid` → `stationmagnitude__parent_oid ON public.stationmagnitude USING btree (_parent_oid)`
- `stationmagnitude_m_amplitudeid` → `stationmagnitude_m_amplitudeid ON public.stationmagnitude USING btree (m_amplitudeid)`
- `stationmagnitude_pkey` → `ÚNICO stationmagnitude_pkey ON public.stationmagnitude USING btree (_oid)`

_Enlaza la cadena preferida:_ `m_originid`, `m_amplitudeid`, `m_waveformid_networkcode`, `m_waveformid_stationcode`

### stationmagnitudecontribution

Detalle de la contribución de cada estación a la magnitud.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_stationmagnitudeid` | character varying |
| `m_residual` | double precision |
| `m_weight` | double precision |

**Índices:**

- `stationmagnitudecontribution__parent_oid` → `stationmagnitudecontribution__parent_oid ON public.stationmagnitudecontribution USING btree (_parent_oid)`
- `stationmagnitudecontribution_composite_index` → `ÚNICO stationmagnitudecontribution_composite_index ON public.stationmagnitudecontribution USING btree (_parent_oid, m_stationmagnitudeid)`
- `stationmagnitudecontribution_m_stationmagnitudeid` → `stationmagnitudecontribution_m_stationmagnitudeid ON public.stationmagnitudecontribution USING btree (m_stationmagnitudeid)`
- `stationmagnitudecontribution_pkey` → `ÚNICO stationmagnitudecontribution_pkey ON public.stationmagnitudecontribution USING btree (_oid)`

### dataused

Resumen de datos empleados en el origen.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_wavetype` | character varying |
| `m_stationcount` | integer |
| `m_componentcount` | integer |
| `m_shortestperiod` | double precision |

**Índices:**

- `dataused__parent_oid` → `dataused__parent_oid ON public.dataused USING btree (_parent_oid)`
- `dataused_pkey` → `ÚNICO dataused_pkey ON public.dataused USING btree (_oid)`

### reading

Lecturas asociadas a un pick.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |

**Índices:**

- `reading__parent_oid` → `reading__parent_oid ON public.reading USING btree (_parent_oid)`
- `reading_pkey` → `ÚNICO reading_pkey ON public.reading USING btree (_oid)`

## INVENTARIO DE ESTACIONES

### network

Red sismológica (nivel superior del inventario).

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_code` | character varying |
| `m_start` | timestamp without time zone |
| `m_start_ms` | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_description` | character varying |
| `m_institutions` | character varying |
| `m_region` | character varying |
| `m_type` | character varying |
| `m_netclass` | character |
| `m_archive` | character varying |
| `m_restricted` | boolean |
| `m_shared` | boolean |
| `m_remark_content` | bytea |
| `m_remark_used` | boolean |

**Índices:**

- `network__parent_oid` → `network__parent_oid ON public.network USING btree (_parent_oid)`
- `network_composite_index` → `ÚNICO network_composite_index ON public.network USING btree (_parent_oid, m_code, m_start, m_start_ms)`
- `network_pkey` → `ÚNICO network_pkey ON public.network USING btree (_oid)`

### station

Estación sismológica.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_code` | character varying |
| `m_start` | timestamp without time zone |
| `m_start_ms` | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_description` | character varying |
| `m_latitude` | double precision |
| `m_longitude` | double precision |
| `m_elevation` | double precision |
| `m_place` | character varying |
| `m_country` | character varying |
| `m_affiliation` | character varying |
| `m_type` | character varying |
| `m_archive` | character varying |
| `m_archivenetworkcode` | character varying |
| `m_restricted` | boolean |
| `m_shared` | boolean |
| `m_remark_content` | bytea |
| `m_remark_used` | boolean |

**Índices:**

- `station__parent_oid` → `station__parent_oid ON public.station USING btree (_parent_oid)`
- `station_composite_index` → `ÚNICO station_composite_index ON public.station USING btree (_parent_oid, m_code, m_start, m_start_ms)`
- `station_pkey` → `ÚNICO station_pkey ON public.station USING btree (_oid)`

### sensorlocation

Emplazamiento dentro de una estación.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_code` | character varying |
| `m_start` | timestamp without time zone |
| `m_start_ms` | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_latitude` | double precision |
| `m_longitude` | double precision |
| `m_elevation` | double precision |

**Índices:**

- `sensorlocation__parent_oid` → `sensorlocation__parent_oid ON public.sensorlocation USING btree (_parent_oid)`
- `sensorlocation_composite_index` → `ÚNICO sensorlocation_composite_index ON public.sensorlocation USING btree (_parent_oid, m_code, m_start, m_start_ms)`
- `sensorlocation_pkey` → `ÚNICO sensorlocation_pkey ON public.sensorlocation USING btree (_oid)`

### stream

Canal (stream) de un emplazamiento.

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_code` | character varying |
| `m_start` | timestamp without time zone |
| `m_start_ms` | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_datalogger` | character varying |
| `m_dataloggerserialnumber` | character varying |
| `m_dataloggerchannel` | integer |
| `m_sensor` | character varying |
| `m_sensorserialnumber` | character varying |
| `m_sensorchannel` | integer |
| `m_clockserialnumber` | character varying |
| `m_sampleratenumerator` | integer |
| `m_sampleratedenominator` | integer |
| `m_depth` | double precision |
| `m_azimuth` | double precision |
| `m_dip` | double precision |
| `m_gain` | double precision |
| `m_gainfrequency` | double precision |
| `m_gainunit` | character varying |
| `m_format` | character varying |
| `m_flags` | character varying |
| `m_restricted` | boolean |
| `m_shared` | boolean |

**Índices:**

- `stream__parent_oid` → `stream__parent_oid ON public.stream USING btree (_parent_oid)`
- `stream_composite_index` → `ÚNICO stream_composite_index ON public.stream USING btree (_parent_oid, m_code, m_start, m_start_ms)`
- `stream_pkey` → `ÚNICO stream_pkey ON public.stream USING btree (_oid)`

## Relaciones clave (matriz)

| De | Columna | Hacia | Nota | Cardinalidad |
| --- | --- | --- | --- | --- |
| `object` | `_oid` | `publicobject` | mismo _oid | 1 : 1 |
| `publicobject` | `_oid` | `origin` | mismo _oid | 1 : 1 |
| `publicobject` | `_oid` | `event` | mismo _oid | 1 : 1 |
| `publicobject` | `_oid` | `magnitude` | mismo _oid | 1 : 1 |
| `publicobject` | `_oid` | `pick` | mismo _oid | 1 : 1 |
| `event` | `m_preferredoriginid` | `origin` | ORIGEN PREFERIDO ★ | N : 0..1 |
| `event` | `m_preferredmagnitudeid` | `magnitude` | magnitud preferida ★ | N : 0..1 |
| `event` | `_oid` | `eventdescription` | descripciones del evento | 1 : N |
| `event` | `_oid` | `originreference` | origenes del evento | 1 : N |
| `originreference` | `m_originid` | `origin` | un origen alternativo | N : 1 |
| `origin` | `_oid` | `arrival` | llegadas del origen ★ | 1 : N |
| `arrival` | `m_pickid` | `pick` | pick usado ★ | N : 0..1 |
| `pick` | `m_waveformid_stationcode` | `station` | qué estación ★ | N : 1 |
| `origin` | `_oid` | `amplitude` | amplitudes del origen | 1 : N |
| `amplitude` | `m_pickid` | `pick` | sobre ese pick | N : 1 |
| `origin` | `m_publicid` | `stationmagnitude` | magnitud por estación ★ | 1 : N |
| `stationmagnitude` | `m_amplitudeid` | `amplitude` | usa esa amplitud | N : 0..1 |
| `magnitude` | `_oid` | `stationmagnitudecontribution` | contribuciones | 1 : N |
| `stationmagnitudecontribution` | `m_stationmagnitudeid` | `stationmagnitude` | de cada estación | N : 1 |
| `origin` | `_oid` | `dataused` | datos usados | 1 : N |
| `pick` | `_oid` | `reading` | lecturas del pick | 1 : N |
| `network` | `_oid` | `station` | st. pertenece a la red | 1 : N |
| `station` | `_oid` | `sensorlocation` | emplazamientos | 1 : N |
| `sensorlocation` | `_oid` | `stream` | canales (streams) | 1 : N |

> ★ = relación de la **solución preferida**. En el diagrama, cada extremo del conector lleva un **símbolo** que indica cuántas filas de la tabla que toca participan en la relación: `1` = una, `N` = varias, `0..1` = cero o una (opcional), `0..N` = cero o varias. En esta tabla la cardinalidad se lee en el sentido De → Hacia (primera etiqueta = tabla De, segunda = Hacia).

### Símbolos de cardinalidad

| Símbolo | Significado |
| --- | --- |
| `1` | una fila de esa tabla participa en la relación |
| `N` | varias filas de esa tabla participan en la relación |
| `0..1` | cero o una (opcional) — como máximo una fila |
| `0..N` | cero o varias (opcional) |

## Anexo — Descripción de cada tabla

> **Contiene.** qué datos viven en la tabla. **Para qué se usa.** su rol dentro del esquema (especialmente en la cadena de la solución preferida). **Atributos.** columnas en orden, con las llaves en negrita (llave = PRIMARY KEY, única = UNIQUE).

### BASE

#### object

- **Contiene.** Dos columnas: `_oid` (identidad global única) y `_timestamp`. Toda tabla de dominio hereda este `_oid`: el objeto se reparte en una fila en `object` y otra en la tabla específica con el mismo `_oid`.
- **Para qué se usa.** Da la identidad compartida: es la forma de relacionar "la misma cosa" entre tablas (event, origin, pick, etc.) sin depender de textos. El `_parent_oid` de las tablas hijas apunta a un `_oid` de acá.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_timestamp` | timestamp without time zone |

#### publicobject

- **Contiene.** `_oid` (idéntico al de `object`) y `m_publicid`, el identificador público textual (p. ej. `Origin/2026-09-07_...`), único e indexado.
- **Para qué se usa.** Es el "puente de nombres" del esquema: las referencias entre objetos se guardan como texto (`m_preferredoriginid`, `m_pickid`, etc.) y `publicobject` permite traducir ese texto al `_oid` numérico (o al revés) con un único lookup por índice. Por eso aparece unido con `object` en la base del diagrama.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`m_publicid`** (única) | character varying |

### NÚCLEO SÍSMICO

#### event

- **Contiene.** Datos generales del evento: tipo (`m_type`), incertidumbre (`m_typecertainty`), agencia/autor, y los punteros a la solución oficial: `m_preferredoriginid`, `m_preferredmagnitudeid`, `m_preferredfocalmechanismid`.
- **Para qué se usa.** Puerta de entrada del análisis: de acá sale la cadena de la SOLUCIÓN PREFERIDA que NewPT consulta. Si el ID que se pasa es de un evento, el script busca su `m_preferredoriginid` para plotear ese origen.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_preferredoriginid` | character varying |
| `m_preferredmagnitudeid` | character varying |
| `m_preferredfocalmechanismid` | character varying |
| `m_type` | character varying |
| `m_typecertainty` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

#### origin

- **Contiene.** Resultado de una localización: tiempo origen (`m_time_value`), latitud, longitud, profundidad, RMS (`m_quality_standarderror`), gap azimutal, cantidad de fases usadas (`m_quality_usedphasecount`), agencia/autor y estado de evaluación (`m_evaluationstatus`).
- **Para qué se usa.** El ORIGEN PREFERIDO es el corazón de la cadena: arrastra sus `arrival` (llegadas), `amplitude`, `stationmagnitude` (magnitudes por estación) y `dataused`. Es la solución que el analista debe Confirmar en SeisComP; si el ID copiado no es el preferido actual, NewPT avisa.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_time_value` | timestamp without time zone |
| `m_time_value_ms` | integer |
| `m_time_uncertainty` | double precision |
| `m_time_loweruncertainty` | double precision |
| `m_time_upperuncertainty` | double precision |
| `m_time_confidencelevel` | double precision |
| `m_time_pdf_variable_content` | bytea |
| `m_time_pdf_probability_content` | bytea |
| `m_time_pdf_used` | boolean |
| `m_latitude_value` | double precision |
| `m_latitude_uncertainty` | double precision |
| `m_latitude_loweruncertainty` | double precision |
| `m_latitude_upperuncertainty` | double precision |
| `m_latitude_confidencelevel` | double precision |
| `m_latitude_pdf_variable_content` | bytea |
| `m_latitude_pdf_probability_content` | bytea |
| `m_latitude_pdf_used` | boolean |
| `m_longitude_value` | double precision |
| `m_longitude_uncertainty` | double precision |
| `m_longitude_loweruncertainty` | double precision |
| `m_longitude_upperuncertainty` | double precision |
| `m_longitude_confidencelevel` | double precision |
| `m_longitude_pdf_variable_content` | bytea |
| `m_longitude_pdf_probability_content` | bytea |
| `m_longitude_pdf_used` | boolean |
| `m_depth_value` | double precision |
| `m_depth_uncertainty` | double precision |
| `m_depth_loweruncertainty` | double precision |
| `m_depth_upperuncertainty` | double precision |
| `m_depth_confidencelevel` | double precision |
| `m_depth_pdf_variable_content` | bytea |
| `m_depth_pdf_probability_content` | bytea |
| `m_depth_pdf_used` | boolean |
| `m_depth_used` | boolean |
| `m_depthtype` | character varying |
| `m_timefixed` | boolean |
| `m_epicenterfixed` | boolean |
| `m_referencesystemid` | character varying |
| `m_methodid` | character varying |
| `m_earthmodelid` | character varying |
| `m_quality_associatedphasecount` | integer |
| `m_quality_usedphasecount` | integer |
| `m_quality_associatedstationcount` | integer |
| `m_quality_usedstationcount` | integer |
| `m_quality_depthphasecount` | integer |
| `m_quality_standarderror` | double precision |
| `m_quality_azimuthalgap` | double precision |
| `m_quality_secondaryazimuthalgap` | double precision |
| `m_quality_groundtruthlevel` | character varying |
| `m_quality_maximumdistance` | double precision |
| `m_quality_minimumdistance` | double precision |
| `m_quality_mediandistance` | double precision |
| `m_quality_used` | boolean |
| `m_uncertainty_horizontaluncertainty` | double precision |
| `m_uncertainty_minhorizontaluncertainty` | double precision |
| `m_uncertainty_maxhorizontaluncertainty` | double precision |
| `m_uncertainty_azimuthmaxhorizontaluncertainty` | double precision |
| `m_uncertainty_confidenceellipsoid_semimajoraxislength` | double precision |
| `m_uncertainty_confidenceellipsoid_semiminoraxislength` | double precision |
| `m_uncertainty_confidenceellipsoid_semiintermediateaxislength` | double precision |
| `m_uncertainty_confidenceellipsoid_majoraxisplunge` | double precision |
| `m_uncertainty_confidenceellipsoid_majoraxisazimuth` | double precision |
| `m_uncertainty_confidenceellipsoid_majoraxisrotation` | double precision |
| `m_uncertainty_confidenceellipsoid_used` | boolean |
| `m_uncertainty_preferreddescription` | character varying |
| `m_uncertainty_confidencelevel` | double precision |
| `m_uncertainty_used` | boolean |
| `m_type` | character varying |
| `m_evaluationmode` | character varying |
| `m_evaluationstatus` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

#### magnitude

- **Contiene.** Valor numérico (`m_magnitude_value`), tipo (ML, Md, Mw…), y referencia al origen del que se calculó (`m_originid`).
- **Para qué se usa.** Representa la magnitud PREFERIDA (`event.m_preferredmagnitudeid`) y agrupa las contribuciones por estación de `stationmagnitudecontribution`. NewPT la muestra en el título del ploteo.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_magnitude_value` | double precision |
| `m_magnitude_uncertainty` | double precision |
| `m_magnitude_loweruncertainty` | double precision |
| `m_magnitude_upperuncertainty` | double precision |
| `m_magnitude_confidencelevel` | double precision |
| `m_magnitude_pdf_variable_content` | bytea |
| `m_magnitude_pdf_probability_content` | bytea |
| `m_magnitude_pdf_used` | boolean |
| `m_type` | character varying |
| `m_originid` | character varying |
| `m_methodid` | character varying |
| `m_stationcount` | integer |
| `m_azimuthalgap` | double precision |
| `m_evaluationstatus` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

#### eventdescription

- **Contiene.** Filas con `m_type` (por ejemplo `region name`) y el texto asociado (`m_text`), vinculadas al evento por `_parent_oid`.
- **Para qué se usa.** Fuente del nombre de la región que aparece en el título del gráfico de NewPT: se toma la fila con `m_type = 'region name'`.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| `m_text` | character varying |
| **`m_type`** (única) | character varying |

#### originreference

- **Contiene.** Cada fila asocia un evento con uno de sus orígenes vía `m_originid` (por ID público); `_parent_oid` apunta al evento.
- **Para qué se usa.** Aclara que un evento "tiene asociados" varios orígenes. Explica por qué NewPT valida que el origen pegado sea el preferido antes de generar el ploteo.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| **`m_originid`** (única) | character varying |

### CADENA DEL ORIGEN PREFERIDO

#### arrival

- **Contiene.** Observación del cálculo del origen: fase (`m_phase_code`, p. ej. `P`/`S`), si se usó en la localización (`m_timeused`), peso (`m_weight`) y el pick que la respalda (`m_pickid`).
- **Para qué se usa.** Hilvana ORIGEN → PICK: cada llegada del origen preferido apunta al `pick` que le da la hora de esa fase. Contar las `arrival` con `m_timeused` da el número de fases usadas del evento.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| **`m_pickid`** (única) | character varying |
| `m_phase_code` | character varying |
| `m_timecorrection` | double precision |
| `m_azimuth` | double precision |
| `m_distance` | double precision |
| `m_takeoffangle` | double precision |
| `m_timeresidual` | double precision |
| `m_horizontalslownessresidual` | double precision |
| `m_backazimuthresidual` | double precision |
| `m_timeused` | boolean |
| `m_horizontalslownessused` | boolean |
| `m_backazimuthused` | boolean |
| `m_weight` | double precision |
| `m_earthmodelid` | character varying |
| `m_preliminary` | boolean |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

#### pick

- **Contiene.** Tiempo de la detección (`m_time_value`), canal completo vía `m_waveformid_networkcode/stationcode/locationcode/streamcode`, fase estimada (`m_phasehint_code`), onset, polaridad y estado de evaluación.
- **Para qué se usa.** Responde "EN QUÉ ESTACIÓN se registró cada fase": el canal (`m_waveformid_stationcode` + `networkcode`) se resuelve contra `station`/`network`. Es el eslabón final de la cadena preferida y la clave del proyecto de revisar los picks por evento.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_time_value` | timestamp without time zone |
| `m_time_value_ms` | integer |
| `m_time_uncertainty` | double precision |
| `m_time_loweruncertainty` | double precision |
| `m_time_upperuncertainty` | double precision |
| `m_time_confidencelevel` | double precision |
| `m_time_pdf_variable_content` | bytea |
| `m_time_pdf_probability_content` | bytea |
| `m_time_pdf_used` | boolean |
| `m_waveformid_networkcode` | character varying |
| `m_waveformid_stationcode` | character varying |
| `m_waveformid_locationcode` | character varying |
| `m_waveformid_channelcode` | character varying |
| `m_waveformid_resourceuri` | character varying |
| `m_filterid` | character varying |
| `m_methodid` | character varying |
| `m_horizontalslowness_value` | double precision |
| `m_horizontalslowness_uncertainty` | double precision |
| `m_horizontalslowness_loweruncertainty` | double precision |
| `m_horizontalslowness_upperuncertainty` | double precision |
| `m_horizontalslowness_confidencelevel` | double precision |
| `m_horizontalslowness_pdf_variable_content` | bytea |
| `m_horizontalslowness_pdf_probability_content` | bytea |
| `m_horizontalslowness_pdf_used` | boolean |
| `m_horizontalslowness_used` | boolean |
| `m_backazimuth_value` | double precision |
| `m_backazimuth_uncertainty` | double precision |
| `m_backazimuth_loweruncertainty` | double precision |
| `m_backazimuth_upperuncertainty` | double precision |
| `m_backazimuth_confidencelevel` | double precision |
| `m_backazimuth_pdf_variable_content` | bytea |
| `m_backazimuth_pdf_probability_content` | bytea |
| `m_backazimuth_pdf_used` | boolean |
| `m_backazimuth_used` | boolean |
| `m_slownessmethodid` | character varying |
| `m_onset` | character varying |
| `m_phasehint_code` | character varying |
| `m_phasehint_used` | boolean |
| `m_polarity` | character varying |
| `m_evaluationmode` | character varying |
| `m_evaluationstatus` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

#### amplitude

- **Contiene.** Valor de amplitud y tipo, asociada a un pick (`m_pickid`), al origen (`_parent_oid`) y con canal de origen (`m_waveformid_*`).
- **Para qué se usa.** Da las mediciones de amplitud por fase, base para magnitudes tipo Mw por estación; alimenta `stationmagnitude`.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_type` | character varying |
| `m_amplitude_value` | double precision |
| `m_amplitude_uncertainty` | double precision |
| `m_amplitude_loweruncertainty` | double precision |
| `m_amplitude_upperuncertainty` | double precision |
| `m_amplitude_confidencelevel` | double precision |
| `m_amplitude_pdf_variable_content` | bytea |
| `m_amplitude_pdf_probability_content` | bytea |
| `m_amplitude_pdf_used` | boolean |
| `m_amplitude_used` | boolean |
| `m_timewindow_reference` | timestamp without time zone |
| `m_timewindow_reference_ms` | integer |
| `m_timewindow_begin` | double precision |
| `m_timewindow_end` | double precision |
| `m_timewindow_used` | boolean |
| `m_period_value` | double precision |
| `m_period_uncertainty` | double precision |
| `m_period_loweruncertainty` | double precision |
| `m_period_upperuncertainty` | double precision |
| `m_period_confidencelevel` | double precision |
| `m_period_pdf_variable_content` | bytea |
| `m_period_pdf_probability_content` | bytea |
| `m_period_pdf_used` | boolean |
| `m_period_used` | boolean |
| `m_snr` | double precision |
| `m_unit` | character varying |
| `m_pickid` | character varying |
| `m_waveformid_networkcode` | character varying |
| `m_waveformid_stationcode` | character varying |
| `m_waveformid_locationcode` | character varying |
| `m_waveformid_channelcode` | character varying |
| `m_waveformid_resourceuri` | character varying |
| `m_waveformid_used` | boolean |
| `m_filterid` | character varying |
| `m_methodid` | character varying |
| `m_scalingtime_value` | timestamp without time zone |
| `m_scalingtime_value_ms` | integer |
| `m_scalingtime_uncertainty` | double precision |
| `m_scalingtime_loweruncertainty` | double precision |
| `m_scalingtime_upperuncertainty` | double precision |
| `m_scalingtime_confidencelevel` | double precision |
| `m_scalingtime_pdf_variable_content` | bytea |
| `m_scalingtime_pdf_probability_content` | bytea |
| `m_scalingtime_pdf_used` | boolean |
| `m_scalingtime_used` | boolean |
| `m_magnitudehint` | character varying |
| `m_evaluationmode` | character varying |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

#### stationmagnitude

- **Contiene.** Magnitud por estación (`m_magnitude_value`, `m_type`), que referencia el origen del evento (`m_originid`) y la amplitud usada (`m_amplitudeid`).
- **Para qué se usa.** Es la contribución individual de cada estación a la magnitud; sirve para auditar cómo se calculó la magnitud del evento.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_originid` | character varying |
| `m_magnitude_value` | double precision |
| `m_magnitude_uncertainty` | double precision |
| `m_magnitude_loweruncertainty` | double precision |
| `m_magnitude_upperuncertainty` | double precision |
| `m_magnitude_confidencelevel` | double precision |
| `m_magnitude_pdf_variable_content` | bytea |
| `m_magnitude_pdf_probability_content` | bytea |
| `m_magnitude_pdf_used` | boolean |
| `m_type` | character varying |
| `m_amplitudeid` | character varying |
| `m_methodid` | character varying |
| `m_waveformid_networkcode` | character varying |
| `m_waveformid_stationcode` | character varying |
| `m_waveformid_locationcode` | character varying |
| `m_waveformid_channelcode` | character varying |
| `m_waveformid_resourceuri` | character varying |
| `m_waveformid_used` | boolean |
| `m_passedqc` | boolean |
| `m_creationinfo_agencyid` | character varying |
| `m_creationinfo_agencyuri` | character varying |
| `m_creationinfo_author` | character varying |
| `m_creationinfo_authoruri` | character varying |
| `m_creationinfo_creationtime` | timestamp without time zone |
| `m_creationinfo_creationtime_ms` | integer |
| `m_creationinfo_modificationtime` | timestamp without time zone |
| `m_creationinfo_modificationtime_ms` | integer |
| `m_creationinfo_version` | character varying |
| `m_creationinfo_used` | boolean |

#### stationmagnitudecontribution

- **Contiene.** Residual, peso y punteros: `_parent_oid` hacia la `magnitude` y `m_stationmagnitudeid` hacia el `stationmagnitude` que contribuye.
- **Para qué se usa.** Permite reconstruir cómo se obtuvo la magnitud preferida a partir de las magnitudes por estación (auditoría del cálculo).

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| **`m_stationmagnitudeid`** (única) | character varying |
| `m_residual` | double precision |
| `m_weight` | double precision |

#### dataused

- **Contiene.** Por tipo de onda (`m_wavetype`, p. ej. `P`, `S`): conteo de estaciones (`m_stationcount`) y componentes (`m_componentcount`) usados, bajo `_parent_oid` del origen.
- **Para qué se usa.** Da el detalle "qué datos se usaron para localizar el origen preferido".

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |
| `_last_modified` | timestamp without time zone |
| `m_wavetype` | character varying |
| `m_stationcount` | integer |
| `m_componentcount` | integer |
| `m_shortestperiod` | double precision |

#### reading

- **Contiene.** Filas auxiliares enlazadas por `_parent_oid` a un `pick`.
- **Para qué se usa.** Información complementaria del proceso automático de lecturas; no participa de forma crítica en la cadena preferida.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| `_parent_oid` | bigint |

### INVENTARIO DE ESTACIONES

#### network

- **Contiene.** Código de red (`m_code`, p. ej. `CO`), tipo y descripción.
- **Para qué se usa.** Agrupa estaciones; el `pick.m_waveformid_networkcode` se resuelve contra el `m_code` de acá para saber la red del canal.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| **`m_code`** (única) | character varying |
| **`m_start`** (única) | timestamp without time zone |
| **`m_start_ms`** (única) | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_description` | character varying |
| `m_institutions` | character varying |
| `m_region` | character varying |
| `m_type` | character varying |
| `m_netclass` | character |
| `m_archive` | character varying |
| `m_restricted` | boolean |
| `m_shared` | boolean |
| `m_remark_content` | bytea |
| `m_remark_used` | boolean |

#### station

- **Contiene.** Código (`m_code`, p. ej. `HEL`), latitud, longitud, elevación, tipo, y pertenencia a la red vía `_parent_oid`.
- **Para qué se usa.** Destino directo de `pick.m_waveformid_stationcode`: responde qué estación registró cada fase; es la referencia geográfica del inventario.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| **`m_code`** (única) | character varying |
| **`m_start`** (única) | timestamp without time zone |
| **`m_start_ms`** (única) | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_description` | character varying |
| `m_latitude` | double precision |
| `m_longitude` | double precision |
| `m_elevation` | double precision |
| `m_place` | character varying |
| `m_country` | character varying |
| `m_affiliation` | character varying |
| `m_type` | character varying |
| `m_archive` | character varying |
| `m_archivenetworkcode` | character varying |
| `m_restricted` | boolean |
| `m_shared` | boolean |
| `m_remark_content` | bytea |
| `m_remark_used` | boolean |

#### sensorlocation

- **Contiene.** Código de emplazamiento (`m_code`, p. ej. `00`), coordenadas y elevación propias, bajo `_parent_oid` de la estación.
- **Para qué se usa.** Segundo nivel del inventario: distingue posiciones/deploy dentro de la misma estación para asignar el canal correcto del pick.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| **`m_code`** (única) | character varying |
| **`m_start`** (única) | timestamp without time zone |
| **`m_start_ms`** (única) | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_latitude` | double precision |
| `m_longitude` | double precision |
| `m_elevation` | double precision |

#### stream

- **Contiene.** Código de canal (`m_code`, p. ej. `HHZ`), frecuencia de muestreo (numerador/denominador), profundidad, ganancia y período de operación, bajo `_parent_oid` del emplazamiento.
- **Para qué se usa.** Nivel hoja del inventario: el `pick.m_waveformid_streamcode` se resuelve acá y materializa la señal física del canal.

**Atributos:**

| Nombre | Tipo de dato |
| --- | --- |
| **`_oid`** (llave) | bigint |
| **`_parent_oid`** (única) | bigint |
| `_last_modified` | timestamp without time zone |
| **`m_code`** (única) | character varying |
| **`m_start`** (única) | timestamp without time zone |
| **`m_start_ms`** (única) | integer |
| `m_end` | timestamp without time zone |
| `m_end_ms` | integer |
| `m_datalogger` | character varying |
| `m_dataloggerserialnumber` | character varying |
| `m_dataloggerchannel` | integer |
| `m_sensor` | character varying |
| `m_sensorserialnumber` | character varying |
| `m_sensorchannel` | integer |
| `m_clockserialnumber` | character varying |
| `m_sampleratenumerator` | integer |
| `m_sampleratedenominator` | integer |
| `m_depth` | double precision |
| `m_azimuth` | double precision |
| `m_dip` | double precision |
| `m_gain` | double precision |
| `m_gainfrequency` | double precision |
| `m_gainunit` | character varying |
| `m_format` | character varying |
| `m_flags` | character varying |
| `m_restricted` | boolean |
| `m_shared` | boolean |
