$(window).on("load", function () {
  setTimeout(function () {
    $('div[data-page-route="Form/User"] span[data-label="Duplicate"]')
      .closest("li")
      .hide();
  }, 1500);
});

$(".dt-scrollable").ready(function () {
  setTimeout(function () {
    var wh = $(window).height();
    var topPosition = wh - $(".page-form").height();

    var final = topPosition - 200;
    $(".dt-scrollable").attr("style", "height: 100px !important");
  }, 10);
});

frappe.ui.keys.add_shortcut({
  description: "Focus on search field",
  shortcut: "alt+f",
  action: () => {
    let d = document.querySelector(
      "div.page-form.flex > div:nth-child(1)> input"
    );
    if (d) {
      d.focus();
    }
  },
});
