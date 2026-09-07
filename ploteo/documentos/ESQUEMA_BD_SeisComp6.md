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

Raíz común de todos los objetos (identidad _oid).

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_timestamp` | timestamp without time zone |

**Índices:**

- `object_pkey` → `ÚNICO object_pkey ON public.object USING btree (_oid)`

### publicobject

Extiende object: añade m_publicid, el ID público (único).

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `m_publicid` | character varying |

**Índices:**

- `publicobject_m_publicid_key` → `ÚNICO publicobject_m_publicid_key ON public.publicobject USING btree (m_publicid)`
- `publicobject_pkey` → `ÚNICO publicobject_pkey ON public.publicobject USING btree (_oid)`

## NÚCLEO SÍSMICO

### event

El sismo agregado. m_preferredoriginid apunta al ORIGEN PREFERIDO.

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

Una solución de hipocentro (la preferida es la que analiza el analista).

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

Magnitud preferida del evento (m_linkea por publicid).

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

Descripciones textuales (m_type='region name' = región).

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

Contexto: lista todos los orígenes asociados al evento.

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

Llegada de una fase usada para localizar; enlaza el pick usado.

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

Detección de una fase en un canal: dice EN QUÉ ESTACIÓN.

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

Amplitud medida sobre un pick.

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

Contribución de cada estación a la magnitud.

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

Fases/datos usados en la localización.

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

Lecturas asociadas (auxiliar).

| Columna | Tipo |
| --- | --- |
| `_oid` | bigint |
| `_parent_oid` | bigint |

**Índices:**

- `reading__parent_oid` → `reading__parent_oid ON public.reading USING btree (_parent_oid)`
- `reading_pkey` → `ÚNICO reading_pkey ON public.reading USING btree (_oid)`

## INVENTARIO DE ESTACIONES

### network

Red sismológica (padre del inventario).

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

Estación: lat/lon/elev, a la que apunta pick.m_waveformid_stationcode.

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

Emplazamiento de la estación.

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

Canal (stream) del emplazamiento.

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

| De | Columna | Hacia | Nota |
| --- | --- | --- | --- |
| `object` | `_oid` | `publicobject` | publicobject._oid = object._oid |
| `publicobject` | `_oid` | `origin` | origin._oid = publicobject._oid |
| `publicobject` | `_oid` | `event` | event._oid = publicobject._oid |
| `publicobject` | `_oid` | `magnitude` | magnitude._oid = publicobject._oid |
| `publicobject` | `_oid` | `pick` | pick._oid = publicobject._oid |
| `event` | `m_preferredoriginid` | `origin` | ORIGEN PREFERIDO ★ |
| `event` | `m_preferredmagnitudeid` | `magnitude` | magnitud preferida ★ |
| `event` | `_oid` | `eventdescription` | eventdescription._parent_oid = event._oid |
| `event` | `_oid` | `originreference` | origenes del evento |
| `originreference` | `m_originid` | `origin` | un origen alternativo |
| `origin` | `_oid` | `arrival` | llegadas del origen ★ |
| `arrival` | `m_pickid` | `pick` | pick usado ★ |
| `pick` | `m_waveformid_stationcode` | `station` | qué estación ★ |
| `origin` | `_oid` | `amplitude` | amplitudes del origen |
| `amplitude` | `m_pickid` | `pick` | sobre ese pick |
| `origin` | `m_publicid` | `stationmagnitude` | magnitud por estación ★ |
| `stationmagnitude` | `m_amplitudeid` | `amplitude` | usa esa amplitud |
| `magnitude` | `_oid` | `stationmagnitudecontribution` | contribuciones |
| `stationmagnitudecontribution` | `m_stationmagnitudeid` | `stationmagnitude` | de cada estación |
| `origin` | `_oid` | `dataused` | datos usados |
| `pick` | `_oid` | `reading` | lecturas del pick |
| `network` | `_oid` | `station` | st. pertenece a la red |
| `station` | `_oid` | `sensorlocation` | emplazamientos |
| `sensorlocation` | `_oid` | `stream` | canales (streams) |

> ★ = relación de la **solución preferida**.
