(function(){
  function applyTheme(t) {
    var doc = document.documentElement;
    doc.classList.remove('light','dark');
    if (t === 'light') doc.classList.add('light');
    else if (t === 'dark') doc.classList.add('dark');
    // if 'system' or unknown, leave classes off so media-query handles it
  }
  var saved = null;
  try { saved = localStorage.getItem('theme'); } catch(e){}
  if (!saved) saved = 'system';
  applyTheme(saved);
  window.setTheme = function(t){
    try { localStorage.setItem('theme', t); } catch(e){}
    applyTheme(t);
  };
})();
