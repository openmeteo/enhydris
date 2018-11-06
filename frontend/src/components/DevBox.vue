<template lang="html">
  <div 
    v-if="mode == 'development'" 
    class="dev-info"
  >
    <div class="tags are-medium">
      <span class="tag is-success">{{ mode }}</span>
      <span class="tag is-link">{{ apiRoot }}</span>
    </div>
  </div>
</template>

<script>
import utils from "../utils";

export default {
  name: "DevBox",
  data: function() {
    return {
      mode: utils.get_app_mode(),
      apiRoot: utils.get_api_root()
    };
  }
};
</script>

<style lang="css" scoped>
  .dev-info {
    padding-left: 2rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
  }
</style>
