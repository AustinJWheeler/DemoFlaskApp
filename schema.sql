create table user
(
  id      integer not null
    constraint user_pk
      primary key autoincrement,
  name    varchar(250),
  email   varchar(250),
  picture varchar(250)
);

