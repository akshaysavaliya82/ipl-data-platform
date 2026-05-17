{% test positive_value(model, column_name) %}

select
    {{ column_name }} as invalid_value,
    count(*) as occurrences
from {{ model }}
where {{ column_name }} < 0
group by {{ column_name }}
having count(*) > 0

{% endtest %}
