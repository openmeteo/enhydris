import { shallowMount, RouterLinkStub } from "@vue/test-utils";
import NavBar from "@/components/layout/NavBar";

describe("NavBar with locale en", () => {
  let wrapper;
  beforeEach(() => {
    wrapper = shallowMount(NavBar, {
      mocks: {
        $t: msg => msg,
        $i18n: { locale: "en" },
        localePath: msg => msg
      },
      stubs: {
        NuxtLink: RouterLinkStub
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

describe("NavBar with admin link", () => {
  let wrapper;
  beforeEach(() => {
    wrapper = shallowMount(NavBar, {
      mocks: {
        $t: msg => msg,
        $i18n: { locale: "en" },
        localePath: msg => msg
      },
      stubs: {
        NuxtLink: RouterLinkStub
      }
    });
  });

  it("has admin link", () => {
    wrapper.setData({ adminLink: "/admin/" });
    expect(wrapper.find("#adminLink").element.text).toContain("login");
  });

  it("renders correctly", () => {
    wrapper.setData({ adminLink: "/admin/" });
    expect(wrapper.element).toMatchSnapshot();
  });
});
