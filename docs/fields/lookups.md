# Lookups

*Lookups* can be used to specify more complex conditions that fields must match when filtering.

Different [types][types] have different lookups available to them. 

## `exact`

[`[text]`][text]
[`[choice]`][choice]
[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]
[`[bool]`][bool]

Return values equal to the search value.

## `ne`
[`[text]`][text]
[`[choice]`][choice]
[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]
[`[bool]`][bool]

Return values not equal to the search value.

## `in`

[`[text]`][text]
[`[choice]`][choice]
[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]
[`[bool]`][bool]

Return values that are within the set of search values.

## `contains`

[`[text]`][text]

Return values that contain the search value.

## `startswith`

[`[text]`][text]

Return values that start with the search value.

## `endswith`

[`[text]`][text]

Return values that end with the search value.

## `iexact`

[`[text]`][text]

Return values case-insensitively equal to the search value.

## `icontains`

[`[text]`][text]

Return values that case-insensitively contain the search value.

## `istartswith`

[`[text]`][text]

Return values that case-insensitively start with the search value.

## `iendswith`

[`[text]`][text]

Return values that case-insensitively end with the search value.

## `regex`

[`[text]`][text]

Return values that match the search regular expression.

## `iregex`

[`[text]`][text]

Return values that case-insensitively match the search regular expression.

## `length`

[`[text]`][text]

Return values with a length equal to the search value.

## `length__in`

[`[text]`][text]

Return values with a length that is within the set of search values.

## `length__range`

[`[text]`][text]

Return values with a length that is within an inclusive range of search values.

## `lt`

[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values less than the search value.

## `lte`

[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values less than or equal to the search value.

## `gt`

[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values greater than the search value.

## `gte`

[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values greater than or equal to the search value.

## `range`

[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values within an inclusive range of search values.

## `year`

[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with a year equal to the search year.

## `year__in`

[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with a year that is within the set of search years.

## `year__range`

[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with a year that is within an inclusive range of search years.

## `iso_year`

[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with an ISO 8601 week-numbering year equal to the search year.

## `iso_year__in`

[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with an ISO 8601 week-numbering year that is within the set of search years.

## `iso_year__range`

[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with an ISO 8601 week-numbering year that is within an inclusive range of search years.

## `week`

[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with an ISO 8601 week number equal to the search number.

## `week__in`

[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with an ISO 8601 week number that is within the set of search numbers.

## `week__range`

[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]

Return values with an ISO 8601 week number that is within an inclusive range of search numbers.

## `isnull`

[`[text]`][text]
[`[choice]`][choice]
[`[integer]`][integer]
[`[decimal]`][decimal]
[`[date (YYYY-MM)]`][date-yyyy-mm]
[`[date (YYYY-MM-DD)]`][date-yyyy-mm-dd]
[`[date (YYYY-MM-DD HH:MM:SS)]`][date-yyyy-mm-dd-hhmmss]
[`[bool]`][bool]
[`[relation]`][relation]

Return values that are empty (`isnull = True`) or non-empty (`isnull = False`). 

* For [`text`][text] and [`choice`][choice] types, 'empty' is defined as the empty string `""`. 
* For the [`relation`][relation] type, 'empty' is defined as there being zero items linked to the record being evaluated.
* For all other types, 'empty' is the SQL `null` value.