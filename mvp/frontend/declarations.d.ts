declare module '*.module.css' {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  interface CSSModuleClasses {
    [key: string]: string
  }
  const classes: CSSModuleClasses
  export default classes
}

// Allow importing plain CSS files for side effects (e.g. library styles).
declare module '*.css'

declare module '*.svg' {
  import type { FC, SVGProps } from 'react'
  const content: FC<SVGProps<SVGSVGElement>>
  export default content
}
