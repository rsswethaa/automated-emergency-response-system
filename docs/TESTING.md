# Testing Plan

## Detector tests
| Input | Expected |
|---|---|
| 1.5g, movement detected | LOW |
| 2.5g, movement detected | MEDIUM |
| 4.5g, movement detected | HIGH |
| 6.5g, no movement | CRITICAL |

## Application tests
- database initialises from schema and seed files
- valid incident creates an incident row
- valid incident also creates one alert audit row
- missing coordinates/impact do not create a record
- resolving an incident changes status to `RESOLVED`
- dashboard orders newest incidents first

## Safety tests
- UI displays prototype-only warning
- documentation does not imply connection to emergency services
- sample thresholds are identified as illustrative

## Future automation
Add `pytest` unit tests for `detector.py`, route tests with Flask's test client, and CI to run tests on pull requests.
