import { mount, RouterLinkStub } from "@vue/test-utils";
import LangPicker from "@/components/layout/LangPicker";

describe("LangPicker with locale en", () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mount(LangPicker, {
      mocks: {
        $t: msg => msg,
        $i18n: { locale: "en" },
        switchLocalePath: msg => msg,
        localePath: msg => msg
      },
      stubs: {
        NuxtLink: RouterLinkStub
      }
    });
  });

  it("renders correctly", () => {
    expect(wrapper.element).toMatchSnapshot();
  });

  it("contains link to Greek", () => {
    expect(wrapper.find(RouterLinkStub).props().to).toBe("el");
  });
});
