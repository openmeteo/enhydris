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
    const vp = enhydris.mapViewport;
    this.leafletMap.fitBounds([[vp[1], vp[0]], [vp[3], vp[2]]]);
  },

  setupMapControls() {
    L.control.scale().addTo(this.leafletMap);
    L.control.mousePosition(
      { position: 'bottomright', emptyString: '' },
    ).addTo(this.leafletMap);
    this.layerControl = L.control.layers(enhydris.mapBaseLayers, {}).addTo(this.leafletMap);
  },

  setupStationsLayer() {
    let url = `${enhydris.rootUrl}stations/kml/`;
    if (enhydris.mapMode === 'many-stations') {
      url += `?q=${enhydris.searchString}`;
    } else if (enhydris.mapMode === 'single-station') {
      url += `?gentity_id=${enhydris.agentityId}`;
    }
    this.stationsLayer = new L.KML(url, { async: true });
    this.leafletMap.addLayer(this.stationsLayer);
    this.layerControl.addOverlay(this.stationsLayer, 'Stations');
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

enhydris.chart = {
  initialize() {
    this.initializeMainChart();
    this.initializeMiniChart();
    this.fetchInitialChartData();
  },

  mapData(data) {
    return data.map((i) => [i.timestamp * 1000, Number(i.value) || 0]);
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
          this.mainChart.updateSeries([
            {
              data: this.mapData(data),
            },
          ]);
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
        height: 100,
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
    };

    this.miniChart = new ApexCharts(
      document.querySelector('#chart-mini'),
      miniChartOptions,
    );
    this.miniChart.render();
  },

  initializeMainChart() {
    const self = this;
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
        height: 230,
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
      colors: [grayColor],
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
          format: 'MMM dd, yyyy',
        },
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
          const mappedData = this.mapData(data);
          this.mainChart.updateSeries([
            {
              data: mappedData,
            },
          ]);
          this.miniChart.updateSeries([
            {
              data: mappedData,
            },
          ]);
        } else {
          this.renderError();
        }
      })
      .catch(() => {
        this.renderError();
      });
  },
};
