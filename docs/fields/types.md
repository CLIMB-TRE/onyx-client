# Types

*Types* in Onyx define the various categories of data which can be stored. 

Each field belongs to a certain type. This dictates what kind of data the field can store (e.g. text, numbers, dates, etc.), as well as what filter operations (i.e. [lookups][lookups]) can be carried out on values of the field.

## `text`

[`[exact]`][exact] 
[`[ne]`][ne]
[`[in]`][in]
[`[notin]`][notin]
[`[contains]`][contains]
[`[startswith]`][startswith]
[`[endswith]`][endswith]
[`[iexact]`][iexact]
[`[icontains]`][icontains]
[`[istartswith]`][istartswith]
[`[iendswith]`][iendswith]
[`[regex]`][regex]
[`[iregex]`][iregex]
[`[length]`][length]
[`[length__in]`][length__in]
[`[length__range]`][length__range]
[`[isnull]`][isnull]

**Examples:** `"C-1234567890"`, `"Details about something"`

## `choice`

[`[exact]`][exact] 
[`[ne]`][ne]
[`[in]`][in]
[`[notin]`][notin]
[`[isnull]`][isnull]

**Examples:** `"ENG"`, `"WALES"`, `"SCOT"`, `"NI"`

## `integer`

[`[exact]`][exact] 
[`[ne]`][ne]
[`[in]`][in]
[`[notin]`][notin]
[`[lt]`][lt]
[`[lte]`][lte]
[`[gt]`][gt]
[`[gte]`][gte]
[`[range]`][range]
[`[isnull]`][isnull]

**Examples:** `1`, `-1`, `123`

## `decimal`

[`[exact]`][exact] 
[`[ne]`][ne]
[`[in]`][in]
[`[notin]`][notin]
[`[lt]`][lt]
[`[lte]`][lte]
[`[gt]`][gt]
[`[gte]`][gte]
[`[range]`][range]
[`[isnull]`][isnull]

**Examples:** `1.234`, `1.0`, `23.456`

## `date`

[`[exact]`][exact] 
[`[ne]`][ne]
[`[in]`][in]
[`[notin]`][notin]
[`[lt]`][lt]
[`[lte]`][lte]
[`[gt]`][gt]
[`[gte]`][gte]
[`[range]`][range]
[`[iso_year]`][iso_year]
[`[iso_year__in]`][iso_year__in]
[`[iso_year__range]`][iso_year__range]
[`[week]`][week]
[`[week__in]`][week__in]
[`[week__range]`][week__range]
[`[isnull]`][isnull]

**Examples:** `"2023-03"`, `"2023-04-05"`, `"2024-01-01"` 

## `datetime`

[`[exact]`][exact] 
[`[ne]`][ne]
[`[in]`][in]
[`[notin]`][notin]
[`[lt]`][lt]
[`[lte]`][lte]
[`[gt]`][gt]
[`[gte]`][gte]
[`[range]`][range]
[`[iso_year]`][iso_year]
[`[iso_year__in]`][iso_year__in]
[`[iso_year__range]`][iso_year__range]
[`[week]`][week]
[`[week__in]`][week__in]
[`[week__range]`][week__range]
[`[isnull]`][isnull]

**Examples:** `"2023-01-01 15:30:03"`, `"2024-01-01 09:30:17"`

## `bool`

[`[exact]`][exact] 
[`[ne]`][ne]
[`[in]`][in]
[`[notin]`][notin]
[`[isnull]`][isnull]

**Examples:** `True`, `False`

## `relation`

[`[isnull]`][isnull]