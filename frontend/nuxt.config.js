module.exports = {
  head: {
    titleTemplate: `%s — Enhydris`,
    meta: [
      { charset: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      {
        hid: "description",
        name: "description",
        content: "Enhydris Client App"
      }
    ],
    link: [
      { rel: "icon", type: "image/x-icon", href: "/favicon.ico" },
      {
        rel: "stylesheet",
        href: "https://unpkg.com/leaflet@1.2.0/dist/leaflet.css"
      }
    ]
  },
  loading: { color: "#3B8070" },
  modules: ["@nuxtjs/dotenv", "@nuxtjs/font-awesome"],
  plugins: [
    "~/plugins/vue-moment",
    "~/plugins/buefy",
    { src: "~/plugins/vue-leaflet", ssr: false }
  ],
  build: {
    extend(config, { isDev, isClient }) {
      if (isDev && isClient) {
        config.module.rules.push({
          enforce: "pre",
          test: /\.(js|vue)$/,
          loader: "eslint-loader",
          exclude: /(node_modules)/
        });
      }
    }
  }
};
