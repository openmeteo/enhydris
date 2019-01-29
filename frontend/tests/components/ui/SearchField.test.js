import { mount } from "@vue/test-utils";
import SearchField from "@/components/ui/SearchField";
import Vue from "vue";
import Buefy from "buefy";

Vue.use(Buefy);

describe("SearchField", () => {
  const wrapper = mount(SearchField, {
    mocks: {
      $t: x => x
    }
  });

  it("renders correctly", () => {
    expect(wrapper.element).toMatchSnapshot();
  });
});
