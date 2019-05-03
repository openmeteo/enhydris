import { shallowMount, createLocalVue } from "@vue/test-utils";
import StationHero from "@/components/stations/StationHero";
import Buefy from "buefy";

const localVue = createLocalVue();
localVue.use(Buefy);

const stationDetailMock = {
  id: 1403,
  water_basin: null,
  water_division: {
    id: 505,
    last_modified: null,
    name: "ΗΠΕΙΡΟΣ             ",
    short_name: "ΗΠΕΙΡΟΣ ",
    remarks: "",
    area: null,
    mpoly: null,
    water_basin: null,
    water_division: null,
    political_division: null
  },
  political_division: {
    id: 306,
    last_modified: null,
    name: "ΗΠΕΙΡΟΥ",
    short_name: "ΗΠΕΙΡΟΥ",
    remarks: "",
    area: null,
    mpoly: null,
    code: "",
    water_basin: null,
    water_division: null,
    political_division: null,
    parent: 84
  },
  stype: [
    {
      id: 1,
      last_modified: "2011-06-22T05:21:32.781442Z",
      descr: "Meteorological [Μετεωρολογικός]"
    }
  ],
  overseers: [],
  last_modified: "2015-06-02T10:29:57.718660Z",
  name: "Agios Spiridonas",
  short_name: "",
  remarks:
    "ADCON S06. Installed in the framework of project IRMA ETCP GR-IT 2007-13\n\n---ALT---\n\nADCON S06. Εγκαταστάθηκε στο πλαίσιο του προγράμματος IRMA ETCP GR-IT 2007-13",
  srid: 4326,
  approximate: false,
  altitude: 10.0,
  asrid: null,
  point: "SRID=4326;POINT (20.87591 39.14904)",
  is_automatic: false,
  start_date: null,
  end_date: null,
  copyright_holder:
    "Decentralised Administration of Epirus and Western Macedonia",
  copyright_years: "2015",
  owner: 12
};

describe("StationHero.test.js", () => {
  let wrapper;

  beforeEach(() => {
    wrapper = shallowMount(StationHero, {
      localVue,
      propsData: {
        data: stationDetailMock
      }
    });
  });

  it('has received ["data"] as the data property', () => {
    expect(wrapper.vm.data).toEqual(stationDetailMock);
  });

  it("has the expected html structure", () => {
    expect(wrapper.element).toMatchSnapshot();
  });
});
