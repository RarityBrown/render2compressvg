# render2compressvg

## About

**render2compressvg** optimizes SVGs for size while preserving visual fidelity. It works by generating PNGs based on the original SVG and iteratively removing attributes from each element. If the rendered PNG matches the original, the attribute deletion is kept, otherwise the attribute is restored. This method ensures lossless compression while potentially removing unnecessary information.



```mermaid
graph TD
    delete("Delete an attribute in an element")-->render("Render a new png")-->compare{"compare two pngs\n is_match()"}
    compare--Ture-->preserve("Preserve the deletion")-->delete
    compare--False-->restore("Restore the attribute")-->delete
    render1("Render the original svg to a png")-->compare
    

```



[toc]

## Usage & Examples

todo



## Todo & Roadmap

tood



