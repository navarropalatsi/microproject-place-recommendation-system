CREATE CONSTRAINT RATED_rating IF NOT EXISTS
FOR ()-[r:RATED]->() REQUIRE r.rating IS NOT NULL;

CREATE CONSTRAINT User_userId IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS NODE KEY;

CREATE CONSTRAINT Place_placeId IF NOT EXISTS
FOR (p:Place) REQUIRE p.placeId IS NODE KEY;

CREATE CONSTRAINT Category_name IF NOT EXISTS
FOR (c:Category) REQUIRE c.name IS NODE KEY;

CREATE CONSTRAINT Feature_name IF NOT EXISTS
FOR (f:Feature) REQUIRE f.name IS NODE KEY;

CREATE INDEX Place_country IF NOT EXISTS
FOR (p:Place) ON (p.country);

CREATE INDEX Place_locality IF NOT EXISTS
FOR (p:Place) ON (p.locality);

CREATE INDEX Place_region IF NOT EXISTS
FOR (p:Place) ON (p.region);

CREATE INDEX Place_confidence IF NOT EXISTS
FOR (p:Place) ON (p.confidence);

CREATE TEXT INDEX Place_name IF NOT EXISTS
FOR (p:Place) ON p.name;