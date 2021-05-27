enhydris.map = {
  create() {
    this.setUpMap();
    this.setupStationsLayer();
  },

  setUpMap() {
    this.leafletMap = L.map('mapid');
    this.setupBaseLayers();
    this.setupViewport();
    this.setupMapControls();
  },

  setupBaseLayers() {
    enhydris.mapBaseLayers[enhydris.mapDefaultBaseLayer].addTo(this.leafletMap);
  },

  setupViewport() {
    const [lon1, lat1, lon2, lat2] = enhydris.mapViewport;
    let newLon1 = lon1;
    if (window.innerWidth > 991 && document.querySelector('.with-search-result')) {
      const container = document.querySelector('.search-content-wrapper');
      const searchResult = document.querySelector('.search-result');
      const searchResultWidth = searchResult.clientWidth;
      const containerStyle = window.getComputedStyle(container);
      const leftPadding = parseInt(containerStyle.paddingLeft, 10);
      const leftMargin = parseInt(containerStyle.marginLeft, 10);
      const availableSpace = window.innerWidth - leftMargin - leftPadding - searchResultWidth;
      newLon1 = lon2 - (window.innerWidth / availableSpace) * (lon2 - lon1);
    }
    this.leafletMap.fitBounds([[lat1, newLon1], [lat2, lon2]]);
  },

  setupMapControls() {
    L.control.scale().addTo(this.leafletMap);
    L.control.mousePosition(
      { position: 'bottomright', emptyString: '' },
    ).addTo(this.leafletMap);
    this.layerControl = L.control.layers(enhydris.mapBaseLayers, {}).addTo(this.leafletMap);
  },

  setupStationsLayer() {
    this.stationsLayer = enhydris.stationsLayer.create();
    this.leafletMap.addLayer(this.stationsLayer);
    this.layerControl.addOverlay(this.stationsLayer, enhydris.strStations);
    this.stationsLayer.fillWithStations();
  },

  listStationsVisibleOnMap() {
    const queryParams = Arg.all();
    queryParams.bbox = this.leafletMap.getBounds().toBBoxString();
    let queryString = '';
    Object.keys(queryParams).forEach((param) => {
      if (Object.prototype.hasOwnProperty.call(queryParams, param)) {
        if (param !== '') {
          if (queryString) {
            queryString += '&';
          }
          queryString += `${param}=${queryParams[param]}`;
        }
      }
    });
    window.location = `${window.location.pathname}?${queryString}`;
  },
};

enhydris.stationsLayer = {
  create() {
    return Object.assign(L.layerGroup(), this);
  },

  async fillWithStations() {
    let url = '/api/stations/';
    if (enhydris.mapMode === 'many-stations') {
      url += `?q=${enhydris.searchString}`;
    } else if (enhydris.mapMode === 'single-station') {
      url += `?gentity_id=${enhydris.agentityId}`;
    }
    for (;;) {
      const response = await axios.get(url); // eslint-disable-line no-await-in-loop
      this.addStationsPageToStationsLayer(response);
      url = response.data.next;
      if (!url) break;
    }
  },

  addStationsPageToStationsLayer(response) {
    response.data.results.forEach(async (station) => {
      const [i, j] = [station.geom.indexOf('('), station.geom.indexOf(')')];
      const [lon, lat] = station.geom.slice(i + 1, j).split(' ').map((x) => parseFloat(x));
      const marker = L.marker([lat, lon]);
      const ownerName = await this.getOwnerName(station.owner);
      marker.bindPopup(`
        <h2>${station.name}</h2>
        <p>Owner: ${ownerName}</p>
        <p><a href="/stations/${station.id}/">Details...</a></p>
      `);
      marker.addTo(this);
    });
  },

  ownerNames: {},

  async getOwnerName(ownerId) {
    if (!(ownerId in this.ownerNames)) {
      const response = await axios.get(`/api/organizations/${ownerId}/`);
      this.ownerNames[ownerId] = response.data.name;
    }
    return this.ownerNames[ownerId];
  },
};

enhydris.chart = {
  initialize() {
    this.initializeMainChart();
    this.initializeMiniChart();
    this.fetchInitialChartData();
  },

  chartSeries(data) {
    return [
      {
        name: 'mean',
        data: data.map((i) => [i.timestamp * 1000, i.mean === null ? null : Number(i.mean)]),
      },
      {
        name: 'max',
        data: data.map((i) => [i.timestamp * 1000, i.max === null ? null : Number(i.max)]),
      },
      {
        name: 'min',
        data: data.map((i) => [i.timestamp * 1000, i.min === null ? null : Number(i.min)]),
      },
    ];
  },

  debounce(func, wait, immediate = false) {
    /* Returns a modified callable that waits a certain amount of time
    (i.e. the value of `wait` parameter) before running the function. If the
    function attempts to execute within the wait time, the call is blocked.

    To read more about it:
    https://educative.io/edpresso/how-to-use-the-debounce-function-in-javascript
    */
    let timeout;

    return (...args) => {
      const later = () => {
        timeout = null;
        if (!immediate) func.apply(this, args);
      };
      const callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(this, args);
    };
  },

  renderError() {
    document.querySelector('#data_holder').innerHTML = `<p>${enhydris.strNoData}</p>`;
  },

  refetchChart({ min, max }) {
    /* Make API call to fetch & populate chart data between two selected
    data points (i.e. start datetime and end datetime).
    */
    const startDate = new Date(min).toISOString().substring(0, 16);
    const endDate = new Date(max).toISOString().substring(0, 16);

    this.mainChart.updateSeries([
      {
        data: [],
      },
    ]);
    fetch(`${enhydris.chartApiUrl}?start_date=${startDate}&end_date=${endDate}`)
      .then((response) => response.json())
      .then((data) => {
        if (data && data[0]) {
          this.mainChart.updateSeries(this.chartSeries(data));
        }
      });
  },

  initializeMiniChart() {
    /* When attempting to select section of the mini ("small") chart,
    the `selection` event of the chart is executed multiple times for each
    mouse drags. Since the `refetchChart` function is part of the `selection`
    event, this causes multiple API calls to the chart endpoint before the user
    has completed the selection. This is not efficient. Thus, by using the
    `debounce` function, we can create another function that delay the execution
    of the `refetchChart` function by a certain amount of milliseconds, in order
    to give the user enough time to complete the selection.
    */
    const debounceRefetchChart = this.debounce(this.refetchChart, 200);
    const blueColor = '#008FFB';
    const miniChartOptions = {
      series: [{
        data: [],
      }],
      chart: {
        id: 'miniChart',
        animations: {
          /* We do not animate the mini chart because there's something wrong when
           * there are missing values, probably a bug.
           */
          enabled: false,
        },
        height: '25%',
        type: 'area',
        brush: {
          target: 'mainChart',
          enabled: true,
        },
        selection: {
          enabled: true,
        },
        events: {
          selection(chartContext, { xaxis }) {
            debounceRefetchChart(xaxis);
          },
        },
      },
      colors: [blueColor],
      fill: {
        type: 'gradient',
        gradient: {
          opacityFrom: 0.91,
          opacityTo: 0.1,
        },
      },
      xaxis: {
        type: 'datetime',
        tooltip: {
          enabled: false,
        },
        labels: {
          show: true,
          datetimeFormatter: {
            year: 'yyyy',
            month: "MMM 'yy",
            day: 'dd MMM',
            hour: 'HH:mm',
          },
        },
      },
      yaxis: {
        tickAmount: 2,
        labels: {
          formatter(val) {
            return val.toFixed(enhydris.precision >= 0 ? enhydris.precision : 0);
          },
        },
      },
      legend: {
        show: false,
      },
    };

    this.miniChart = new ApexCharts(
      document.querySelector('#chart-mini'),
      miniChartOptions,
    );
    this.miniChart.render();
  },

  initializeMainChart() {
    const self = this;
    const lightColor = '#CCCCCC';
    const grayColor = '#546E7A';
    const mainChartOption = {
      series: [{
        data: [],
      }],
      noData: {
        text: enhydris.strLoading,
      },
      chart: {
        id: 'mainChart',
        type: 'line',
        height: '75%',
        zoom: {
          type: 'x',
          enabled: true,
          autoScaleYaxis: true,
        },
        toolbar: {
          autoSelected: 'zoom',
          show: true,
          tools: {
            download: true,
            zoomin: true,
            zoomout: true,
            pan: false,
            reset: false,
          },
        },
        events: {
          zoomed(chartContext, { xaxis }) {
            self.refetchChart(xaxis);
            self.miniChart.updateOptions({
              chart: {
                selection: {
                  xaxis,
                },
              },
            });
          },
        },
      },
      colors: [grayColor, lightColor, lightColor],
      stroke: {
        width: 2,
      },
      dataLabels: {
        enabled: false,
      },
      fill: {
        opacity: 1,
      },
      markers: {
        size: 0,
      },
      xaxis: {
        type: 'datetime',
        tooltip: {
          enabled: false,
        },
      },
      yaxis: {
        labels: {
          formatter(val) {
            return val.toFixed(enhydris.precision >= 0 ? enhydris.precision : 0);
          },
        },
      },
      tooltip: {
        enabled: true,
        x: {
          show: true,
          format: 'dd MMM yyyy HH:mm',
        },
      },
      legend: {
        show: false,
      },
    };
    this.mainChart = new ApexCharts(
      document.querySelector('#chart-main'),
      mainChartOption,
    );
    this.mainChart.render();
  },

  fetchInitialChartData() {
    fetch(enhydris.chartApiUrl)
      .then((response) => response.json())
      .then((data) => {
        if (data && data[0]) {
          const series = this.chartSeries(data);
          this.mainChart.updateSeries(series);
          this.miniChart.updateSeries(series.filter((item) => item.name === 'mean'));
        } else {
          this.renderError();
        }
      })
      .catch(() => {
        this.renderError();
      });
  },
};
