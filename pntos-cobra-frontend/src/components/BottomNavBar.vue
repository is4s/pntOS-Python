<template>
  <div class="bottom-navbar">
    <img src="@/assets/branding/Cobra_Logo-Standards_Horizontal-White-Tagline_Vers1.png"
        alt="Cobra: powered by pntOS"
        class="navbar-logo"
      />
  </div>
</template>

<style scoped>
  .bottom-navbar {
    height: var(--footer-height);
    width: 100vw;
    bottom: 0;
    background: linear-gradient(90deg, var(--dark-violet) 0%, var(--dark-violet-gradient) 100%);
    display: flex;
    left: 0;
    align-items: center;
  }

  .navbar-logo {
    width: 418px;
    height: 131px;
    padding-right: 30px;
    margin-left: 30px;
  }

</style>
