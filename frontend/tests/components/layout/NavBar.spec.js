import { shallowMount } from "@vue/test-utils";
import NavBar from "@/components/layout/NavBar";

describe("NavBar with locale en", () => {
  let wrapper;
  beforeEach(() => {
    wrapper = shallowMount(NavBar, {
      mocks: {
        $t: msg => msg,
        $i18n: { locale: "en" }
      }
    });
  });

  it("has default language en", () => {
    expect(wrapper.vm.currentLanguage).toEqual("en");
  });

  it("renders $t('home')", () => {
    expect(wrapper.find("#home").element.text).toContain("home");
  });

  it("renders correctly", () => {
    expect(wrapper.element).toMatchSnapshot();
  });
});
