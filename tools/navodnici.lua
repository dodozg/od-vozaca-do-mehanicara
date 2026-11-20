-- Hrvatski navodnici: „dvostruki” i ‚jednostruki’. Kod se ne dira jer ga Pandoc ne raščlanjuje.
function Quoted(el)
  local otvori, zatvori = "„", "”"
  if el.quotetype == "SingleQuote" then otvori, zatvori = "‚", "’" end
  local r = pandoc.List({pandoc.Str(otvori)})
  r:extend(el.content)
  r:insert(pandoc.Str(zatvori))
  return r
end
