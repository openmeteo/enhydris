export default function({ app }) {
  app.i18n.beforeLanguageSwitch = (oldLocale, newLocale) => {
    app.store.dispatch("language/UPDATE_LANGUAGE", newLocale);
  };
}
