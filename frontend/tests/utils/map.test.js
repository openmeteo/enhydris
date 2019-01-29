import maputils from "../../utils/map.js";

describe("convert2coords", () => {
  it("converts WKT to array", () =>
    expect(
      maputils.convert2coords("SRID=4326;POINT (20.984238 93.147111)")
    ).toEqual([93.147111, 20.984238]));
});
