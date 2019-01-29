import indexpage from "../../pages/index.vue";

describe("Index page", () => {
  it("has a created hook", () => {
    expect(typeof indexpage.created).toBe("function");
  });
});
