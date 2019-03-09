import enTranslations from "./locales/en.json";
import elTranslations from "./locales/el";

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
  modules: [
    "@nuxtjs/dotenv",
    "nuxt-buefy",
    "@nuxtjs/font-awesome",
    [
      "nuxt-i18n",
      {
        locales: [
          {
            code: "el",
            name: "EL",
            iso: "el"
          },
          {
            code: "en",
            name: "EN",
            iso: "en-US"
          }
        ],
        strategy: "prefix_except_default",
        defaultLocale: "en",
        vueI18n: {
          fallbackLocale: "en",
          messages: {
            en: enTranslations,
            el: elTranslations
          }
        }
      }
    ]
  ],
  plugins: [{ src: "~/plugins/vue-leaflet", ssr: false }],
  buefy: {
    materialDesignIcons: false,
    defaultIconPack: "fa"
  },
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
