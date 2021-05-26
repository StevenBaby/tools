from pypika import MySQLQuery as Query
from pypika import Table
from pypika import Field
from pypika.enums import Order

table1 = Table('table_1', alias='t1')

query = Query.from_(table1).select(
    table1.id,
    table1.hello,
)

print(query)

query = query.orderby(table1.id, order=Order.desc)

print(query)

query = query.limit(1)

print(query)

query = query.where(table1.id == 1234)

print(query)

if True:
    query = query.where(table1.content.like(r"%ads"))
    print(query)

if True:
    table2 = Table('table2', alias='t2')
    query = query.left_join(table2).on(
        table1.some_id == table2.id
    ).select(
        table2.id,
        table2.some_field
    ).where(
        table2.some_filter == 1234
    )
    print(query)


print(query)
