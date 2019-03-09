import maputils from "../../utils/map.js";

describe("wkt2coordinates", () => {
  it("converts WKT to array", () =>
    expect(
      maputils.wkt2coordinates("SRID=4326;POINT (20.984238 93.147111)")
    ).toEqual([93.147111, 20.984238]));
});
