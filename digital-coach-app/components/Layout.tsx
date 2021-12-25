import Head from "next/head";
import styles from "./layout.module.css";
import { PropsWithChildren } from "react";
import NavBar from "./NavBar";

export const siteTitle = "Digital Coach";

export default function Layout({ children }: PropsWithChildren<{}>) {
  return (
    <>
      <Head>
        <title>Digital Doach</title>
        <meta name="description" content="Senior Design" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <NavBar />
      <div className={styles.container}>
        <Head>
          <title>{siteTitle}</title>
        </Head>

        <main>{children}</main>
      </div>
    </>
  );
}