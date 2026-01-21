CREATE CONSTRAINT RATED_rating
FOR ()-[r:RATED]->() REQUIRE r.rating IS NOT NULL

CREATE CONSTRAINT user_userId
FOR (u:User) REQUIRE u.userId IS NOT NULL

CREATE CONSTRAINT user_userId
FOR (u:User) REQUIRE u.userId IS UNIQUE

CREATE CONSTRAINT place_placeId
FOR (p:Place) REQUIRE p.placeId IS NOT NULL

CREATE CONSTRAINT place_placeId
FOR (p:Place) REQUIRE p.placeId IS UNIQUE

CREATE CONSTRAINT category_name
FOR (c:Category) REQUIRE c.name IS NOT NULL

CREATE CONSTRAINT category_name
FOR (c:Category) REQUIRE c.name IS UNIQUE

CREATE CONSTRAINT feature_name
FOR (f:Feature) REQUIRE f.name IS NOT NULL

CREATE CONSTRAINT feature_name
FOR (f:Feature) REQUIRE f.name IS UNIQUE