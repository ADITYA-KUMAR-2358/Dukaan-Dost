import { Link } from "react-router-dom";

export function BrandMark({ className = "", markClassName = "" }: { className?: string; markClassName?: string }) {
  return (
    <Link
      to="/"
      aria-label="DukaanDost home"
      onClick={(event) => {
        if (window.location.pathname === "/") {
          event.preventDefault();
          window.history.pushState(null, "", "/");
        }
        window.scrollTo({ top: 0 });
      }}
      className={`wordmark flex min-w-0 items-center gap-2 leading-none ${className}`}
    >
      <img className={`mark ${markClassName}`} src="/favicon.svg" alt="" />
      <span className="truncate">DukaanDost</span>
    </Link>
  );
}
